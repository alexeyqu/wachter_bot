from datetime import datetime, timedelta
import random
from telegram import Bot, Message, ParseMode, Update
from telegram.ext import CallbackContext

from src.logging import tg_logger
from src import constants
from src.model import Chat, User, session_scope


def on_new_chat_members(update: Update, context: CallbackContext) -> None:
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
            if job.context["user_id"] == user_id and job.context["chat_id"] == chat_id:
                job.schedule_removal()

        with session_scope() as sess:
            user = (
                sess.query(User)
                .filter(User.chat_id == chat_id, User.user_id == user_id)
                .first()
            )
            chat = sess.query(Chat).filter(Chat.id == chat_id).first()

            if chat is None:
                chat = Chat(id=chat_id)
                sess.add(chat)
                sess.commit()

            if user is not None:
                update.message.reply_text(chat.on_known_new_chat_member_message)
                continue

            message = chat.on_new_chat_member_message
            kick_timeout = chat.kick_timeout
            notify_timeout = chat.notify_timeout

        if message == constants.skip_on_new_chat_member_message:
            continue

        message_markdown = _mention_markdown(context.bot, chat_id, user_id, message)
        msg = update.message.reply_text(message_markdown, parse_mode=ParseMode.MARKDOWN)

        if kick_timeout != 0:
            job = context.job_queue.run_once(
                on_kick_timeout,
                kick_timeout * 60,
                context={
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "message_id": msg.message_id,
                    "creation_time": datetime.now().timestamp(),
                },
            )

        if notify_timeout != 0:
            job = context.job_queue.run_once(
                on_notify_timeout,
                notify_timeout * 60,
                context={
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "job_queue": context.job_queue,
                    "creation_time": datetime.now().timestamp(),
                },
            )


def on_hashtag_message(update: Update, context: CallbackContext) -> None:
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

    if (
        "#whois" in update.message.parse_entities(types=["hashtag"]).values()
        and chat_id < 0
    ):
        user_id = update.message.from_user.id

        with session_scope() as sess:
            chat = sess.query(Chat).filter(Chat.id == chat_id).first()

            if chat is None:
                chat = Chat(id=chat_id)
                sess.add(chat)
                sess.commit()

            if len(update.message.text) <= chat.whois_length:
                message_markdown = _mention_markdown(
                    # TODO move to chat DB
                    context.bot,
                    chat_id,
                    user_id,
                    constants.on_short_whois_message.format(
                        whois_length=chat.whois_length
                    ),
                )
                update.message.reply_text(
                    message_markdown, parse_mode=ParseMode.MARKDOWN
                )
                return

            message = chat.on_introduce_message

        with session_scope() as sess:
            existing_user = (
                sess.query(User)
                .filter(User.chat_id == chat_id, User.user_id == user_id)
                .first()
            )
            if (
                existing_user
                and "#update"
                not in update.message.parse_entities(types=["hashtag"]).values()
            ):
                message_markdown = _mention_markdown(
                    context.bot, chat_id, user_id, constants.on_introduce_message_update
                )
                update.message.reply_text(
                    message_markdown, parse_mode=ParseMode.MARKDOWN
                )
                return

            user = User(chat_id=chat_id, user_id=user_id, whois=update.message.text)
            sess.merge(user)

        removed = False
        for job in context.job_queue.jobs():
            if job.context["user_id"] == user_id and job.context["chat_id"] == chat_id:
                if "message_id" in job.context:
                    try:
                        context.bot.delete_message(
                            job.context["chat_id"], job.context["message_id"]
                        )
                    except Exception as e:
                        tg_logger.warning(
                            f"can't delete {job.context['message_id']} from {job.context['chat_id']}",
                            exc_info=e,
                        )
                job.schedule_removal()
                removed = True

        if removed:
            message_markdown = _mention_markdown(context.bot, chat_id, user_id, message)
            update.message.reply_text(message_markdown, parse_mode=ParseMode.MARKDOWN)


def on_notify_timeout(context: CallbackContext):
    """
    Send notify message, schedule its deletion.

    Args:
    context (CallbackContext): The context object containing the job details and bot instance.

    Returns:
    None
    """
    bot, job = context.bot, context.job
    with session_scope() as sess:
        chat = sess.query(Chat).filter(Chat.id == job.context["chat_id"]).first()

        message_markdown = _mention_markdown(
            bot, job.context["chat_id"], job.context["user_id"], chat.notify_message
        )

        message = bot.send_message(
            job.context["chat_id"], text=message_markdown, parse_mode=ParseMode.MARKDOWN
        )

        job.context["job_queue"].run_once(
            _delete_message,
            (chat.kick_timeout - chat.notify_timeout) * 60,
            context={
                "chat_id": job.context["chat_id"],
                "user_id": job.context["user_id"],
                "message_id": message.message_id,
            },
        )


def on_kick_timeout(context: CallbackContext) -> None:
    """
    Kick a user from the chat after a set amount of time and send a message about it.

    Args:
    context (CallbackContext): The context object containing the job details and bot instance.

    Returns:
    None
    """
    bot, job = context.bot, context.job
    try:
        bot.delete_message(job.context["chat_id"], job.context["message_id"])
    except Exception as e:
        tg_logger.warning(
            f"can't delete {job.context['message_id']} from {job.context['chat_id']}",
            exc_info=e,
        )

    try:
        bot.kick_chat_member(
            job.context["chat_id"],
            job.context["user_id"],
            until_date=datetime.now() + timedelta(seconds=60),
        )

        with session_scope() as sess:
            chat = sess.query(Chat).filter(Chat.id == job.context["chat_id"]).first()

            if chat.on_kick_message.lower() not in ["false", "0"]:
                message_markdown = _mention_markdown(
                    bot,
                    job.context["chat_id"],
                    job.context["user_id"],
                    chat.on_kick_message,
                )
                if job.context["chat_id"] == constants.RH_CHAT_ID:
                    message_markdown = _mention_markdown(
                        bot,
                        job.context["chat_id"],
                        job.context["user_id"],
                        random.choice(constants.RH_kick_messages),
                    )
                bot.send_message(
                    job.context["chat_id"],
                    text=message_markdown,
                    parse_mode=ParseMode.MARKDOWN,
                )
    except Exception as e:
        tg_logger.exception(e)
        bot.send_message(job.context["chat_id"], text=constants.on_failed_kick_response)


def _delete_message(context: CallbackContext) -> None:
    """
    Delete a message from a chat.

    Args:
    context (CallbackContext): The context object containing the job details and bot instance.

    Returns:
    None
    """
    bot, job = context.bot, context.job
    try:
        bot.delete_message(job.context["chat_id"], job.context["message_id"])
    except Exception as e:
        tg_logger.warning(
            f"can't delete {job.context['message_id']} from {job.context['chat_id']}",
            exc_info=e,
        )


def _mention_markdown(bot: Bot, chat_id: int, user_id: int, message: Message) -> str:
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
    user = bot.get_chat_member(chat_id, user_id).user
    if not user.name:
        # если пользователь удален, у него пропадает имя и markdown выглядит так: (tg://user?id=666)
        user_mention_markdown = ""
    else:
        user_mention_markdown = user.mention_markdown()

    # \ нужен из-за формата сообщений в маркдауне
    return message.replace("%USER\_MENTION%", user_mention_markdown)
