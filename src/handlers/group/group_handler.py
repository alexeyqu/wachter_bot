from datetime import datetime, timedelta
import random
from telegram import Bot, Message, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from sqlalchemy import select

from src.logging import tg_logger
from src import constants
from src.texts import _
from src.model import Chat, User, session_scope


async def on_new_chat_members(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handle the event when a new member joins a chat.

    Args:
    update (Update): The update object that represents the incoming update.
    context (CallbackContext): The context object that contains information about the current state of the bot.

    Returns:
    None
    """
    chat_id = update.message.chat_id
    user_ids = [
        new_chat_member.id for new_chat_member in update.message.new_chat_members
    ]

    for user_id in user_ids:
        for job in context.job_queue.jobs():
            if job.user_id == user_id and job.chat_id == chat_id:
                job.schedule_removal()

        async with session_scope() as sess:
            result = await sess.execute(
                select(User).where(User.chat_id == chat_id, User.user_id == user_id)
            )
            user = result.scalars().first()
            chat_result = await sess.execute(select(Chat).where(Chat.id == chat_id))
            chat = chat_result.scalars().first()

            if chat is None:
                chat = Chat(id=chat_id)
                sess.add(chat)
                await sess.commit()

            if user is not None:
                message = await update.message.reply_text(
                    chat.on_known_new_chat_member_message
                )

                context.job_queue.run_once(
                    delete_message,
                    constants.default_delete_message * 60,  # 1h
                    chat_id=chat_id,
                    user_id=user_id,
                    data={
                        "message_id": message.message_id,
                    },
                )
                continue

            message = chat.on_new_chat_member_message
            kick_timeout = chat.kick_timeout
            notify_timeout = chat.notify_timeout

        if message == _("msg__skip_new_chat_member"):
            continue

        message_markdown = await _mention_markdown(
            context.bot, chat_id, user_id, message
        )
        msg = await update.message.reply_text(
            message_markdown, parse_mode=ParseMode.MARKDOWN
        )

        if kick_timeout != 0:
            job = context.job_queue.run_once(
                on_kick_timeout,
                kick_timeout * 60,
                chat_id=chat_id,
                user_id=user_id,
                data={
                    "message_id": msg.message_id,
                    "creation_time": datetime.now().timestamp(),
                },
            )

        if notify_timeout != 0:
            job = context.job_queue.run_once(
                on_notify_timeout,
                notify_timeout * 60,
                chat_id=chat_id,
                user_id=user_id,
                data={
                    "job_queue": context.job_queue,
                    "creation_time": datetime.now().timestamp(),
                },
            )


async def on_hashtag_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handle messages containing #whois hashtag.

    Args:
    update (Update): The update object that represents the incoming update.
    context (CallbackContext): The context object that contains information about the current state of the bot.

    Returns:
    None
    """
    # If the message was edited, update the message in the update object
    if not update.message:
        update.message = update.edited_message

    chat_id = update.message.chat_id
    parsed_entities = await update.message.parse_entities(types=["hashtag"])
    if (
        "#whois" in parsed_entities.values()
        and chat_id < 0
    ):
        user_id = update.message.from_user.id

        async with session_scope() as sess:
            chat_result = await sess.execute(select(Chat).where(Chat.id == chat_id))
            chat = chat_result.scalars().first()
            if chat is None:
                chat = Chat(id=chat_id)
                sess.add(chat)
                await sess.commit()

            if len(update.message.text) <= chat.whois_length:
                message_markdown = await _mention_markdown(
                    # TODO move to chat DB
                    context.bot,
                    chat_id,
                    user_id,
                    _("msg__short_whois").format(whois_length=chat.whois_length),
                )
                message = await update.message.reply_text(
                    message_markdown, parse_mode=ParseMode.MARKDOWN
                )

                context.job_queue.run_once(
                    delete_message,
                    constants.default_delete_message * 60,  # 1h
                    chat_id=chat_id,
                    user_id=user_id,
                    data={
                        "message_id": message.message_id,
                    },
                )
                return

            message = chat.on_introduce_message

        async with session_scope() as sess:
            result = await sess.execute(
                select(User).where(User.chat_id == chat_id, User.user_id == user_id)
            )
            existing_user = result.scalars().first()
            if (
                existing_user
                and "#update"
                not in await update.message.parse_entities(types=["hashtag"]).values()
            ):
                message_markdown = await _mention_markdown(
                    context.bot, chat_id, user_id, _("msg__introduce_message_update")
                )
                message = await update.message.reply_text(
                    message_markdown, parse_mode=ParseMode.MARKDOWN
                )

                context.job_queue.run_once(
                    delete_message,
                    constants.default_delete_message * 60,  # 1h
                    chat_id=chat_id,
                    user_id=user_id,
                    data={
                        "message_id": message.message_id,
                    },
                )
                return

            user = User(chat_id=chat_id, user_id=user_id, whois=update.message.text)
            await sess.merge(user)

        removed = False
        for job in context.job_queue.jobs():
            if job.user_id == user_id and job.chat_id == chat_id:
                if "message_id" in job.data:
                    try:
                        await context.bot.delete_message(
                            job.chat_id, job.data["message_id"]
                        )
                    except Exception as e:
                        tg_logger.warning(
                            f"can't delete {job.data['message_id']} from {job.chat_id}",
                            exc_info=e,
                        )
                job.schedule_removal()
                removed = True

        if removed:
            message_markdown = await _mention_markdown(
                context.bot, chat_id, user_id, message
            )
            message = await update.message.reply_text(
                message_markdown, parse_mode=ParseMode.MARKDOWN
            )

            context.job_queue.run_once(
                delete_message,
                constants.default_delete_message * 60,  # 1h
                data={
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "message_id": message.message_id,
                },
            )


async def on_notify_timeout(context: ContextTypes.DEFAULT_TYPE):
    """
    Send notify message, schedule its deletion.

    Args:
    context (CallbackContext): The context object containing the job details and bot instance.

    Returns:
    None
    """
    bot, job = context.bot, context.job
    async with session_scope() as sess:
        chat_result = await sess.execute(
            select(Chat).filter(Chat.id == job.data["chat_id"])
        )
        chat = chat_result.scalar_one_or_none()

        message_markdown = await _mention_markdown(
            bot, job.chat_id, job.user_id, chat.notify_message
        )

        message = await bot.send_message(
            job.chat_id, text=message_markdown, parse_mode=ParseMode.MARKDOWN
        )

        job.data["job_queue"].run_once(
            delete_message,
            (chat.kick_timeout - chat.notify_timeout) * 60,
            data={
                "chat_id": job.data["chat_id"],
                "user_id": job.data["user_id"],
                "message_id": message.message_id,
            },
        )


async def on_kick_timeout(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Kick a user from the chat after a set amount of time and send a message about it.

    Args:
    context (CallbackContext): The context object containing the job details and bot instance.

    Returns:
    None
    """
    bot, job = context.bot, context.job
    try:
        await bot.delete_message(job.chat_id, job.data["message_id"])
    except Exception as e:
        tg_logger.warning(
            f"can't delete {job.data['message_id']} from {job.chat_id}",
            exc_info=e,
        )

    try:
        await bot.ban_chat_member(
            job.chat_id,
            job.user_id,
            until_date=datetime.now() + timedelta(seconds=60),
        )

        async with session_scope() as sess:
            chat_result = await sess.execute(select(Chat).where(Chat.id == job.chat_id))
            chat = chat_result.scalar_one_or_none()

            if chat.on_kick_message.lower() not in ["false", "0"]:
                message_markdown = await _mention_markdown(
                    bot,
                    job.chat_id,
                    job.user_id,
                    chat.on_kick_message,
                )
                message = await bot.send_message(
                    job.chat_id,
                    text=message_markdown,
                    parse_mode=ParseMode.MARKDOWN,
                )

                context.job_queue.run_once(
                    delete_message,
                    constants.default_delete_message * 60,  # 1h
                    chat_id=job.chat_id,
                    user_id=job.user_id,
                    data={
                        "message_id": message.message_id,
                    },
                )
    except Exception as e:
        tg_logger.exception(e)
        message = await bot.send_message(
            job.chat_id, text=_("msg__failed_kick_response")
        )

        context.job_queue.run_once(
            delete_message,
            constants.default_delete_message * 60,  # 1h
            data={
                "message_id": message.message_id,
            },
        )


async def delete_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Delete a message from a chat.

    Args:
    context (CallbackContext): The context object containing the job details and bot instance.

    Returns:
    None
    """
    bot, job = context.bot, context.job
    try:
        await bot.delete_message(job.data["chat_id"], job.data["message_id"])
    except Exception as e:
        tg_logger.warning(
            f"can't delete {job.data['message_id']} from {job.chat_id}",
            exc_info=e,
        )


async def _mention_markdown(
    bot: Bot, chat_id: int, user_id: int, message: Message
) -> str:
    """
    Format a message to include a markdown mention of a user.

    Args:
    bot (Bot): The Telegram bot instance.
    chat_id (int): The ID of the chat.
    user_id (int): The ID of the user to mention.
    message (Message): The message to format.

    Returns:
    str: The formatted message with the user mention.
    """
    chat_member = await bot.get_chat_member(chat_id, user_id)
    user = chat_member.user
    if not user.name:
        # если пользователь удален, у него пропадает имя и markdown выглядит так: (tg://user?id=666)
        user_mention_markdown = ""
    else:
        user_mention_markdown = user.mention_markdown()

    # \ нужен из-за формата сообщений в маркдауне
    return message.replace("%USER_MENTION%", user_mention_markdown)
