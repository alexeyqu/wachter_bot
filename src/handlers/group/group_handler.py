from datetime import datetime, timedelta
import logging
import random
from telegram import Bot, Message, ParseMode, Update
from telegram.ext import CallbackContext

from src import constants
from src.model import Chat, User, session_scope


logger = logging.getLogger(__name__)


def on_new_chat_member(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user_id = update.message.new_chat_members[-1].id

    for job in context.job_queue.jobs():
        if (
            job.context["user_id"] == user_id
            and job.context["chat_id"] == chat_id
            and job.enabled == True
        ):
            job.enabled = False
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
            return

        message = chat.on_new_chat_member_message
        timeout = chat.kick_timeout

    if message == constants.skip_on_new_chat_member_message:
        return

    message_markdown = _mention_markdown(context.bot, chat_id, user_id, message)
    msg = update.message.reply_text(message_markdown, parse_mode=ParseMode.MARKDOWN)

    if timeout != 0:
        if timeout >= 10:
            job = context.job_queue.run_once(
                _on_notify_timeout,
                (timeout - constants.notify_delta) * 60,
                context={
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "job_queue": context.job_queue,
                },
            )

        job = context.job_queue.run_once(
            _on_kick_timeout,
            timeout * 60,
            context={
                "chat_id": chat_id,
                "user_id": user_id,
                "message_id": msg.message_id,
            },
        )


def on_hashtag_message(update: Update, context: CallbackContext):
    if not update.message:
        update.message = update.edited_message

    chat_id = update.message.chat_id

    if (
        "#whois" in update.message.parse_entities(types=["hashtag"]).values()
        and len(update.message.text) >= constants.min_whois_length
        and chat_id < 0
    ):
        user_id = update.message.from_user.id

        with session_scope() as sess:
            chat = sess.query(Chat).filter(Chat.id == chat_id).first()

            if chat is None:
                chat = Chat(id=chat_id)
                sess.add(chat)
                sess.commit()

            message = chat.on_introduce_message

        with session_scope() as sess:
            user = User(chat_id=chat_id, user_id=user_id, whois=update.message.text)
            sess.merge(user)

        removed = False
        for job in context.job_queue.jobs():
            if (
                job.context["user_id"] == user_id
                and job.context["chat_id"] == chat_id
                and job.enabled == True
            ):
                try:
                    context.bot.delete_message(
                        job.context["chat_id"], job.context["message_id"]
                    )
                except:
                    pass
                job.enabled = False
                job.schedule_removal()
                removed = True

        if removed:
            message_markdown = _mention_markdown(context.bot, chat_id, user_id, message)
            update.message.reply_text(message_markdown, parse_mode=ParseMode.MARKDOWN)


def _on_notify_timeout(context: CallbackContext):
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
            constants.notify_delta * 60,
            context={
                "chat_id": job.context["chat_id"],
                "user_id": job.context["user_id"],
                "message_id": message.message_id,
            },
        )


def _on_kick_timeout(context: CallbackContext):
    bot, job = context.bot, context.job
    try:
        bot.delete_message(job.context["chat_id"], job.context["message_id"])
    except:
        pass

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
        logger.error(e)
        bot.send_message(job.context["chat_id"], text=constants.on_failed_kick_response)


def _delete_message(context: CallbackContext):
    bot, job = context.bot, context.job
    try:
        bot.delete_message(job.context["chat_id"], job.context["message_id"])
    except:
        print(f"can't delete {job.context['message_id']} from {job.context['chat_id']}")


def _mention_markdown(bot: Bot, chat_id: int, user_id: int, message: Message):
    user = bot.get_chat_member(chat_id, user_id).user
    if not user.name:
        # если пользователь удален, у него пропадает имя и markdown выглядит так: (tg://user?id=666)
        user_mention_markdown = ""
    else:
        user_mention_markdown = user.mention_markdown()

    # \ нужен из-за формата сообщений в маркдауне
    return message.replace("%USER\_MENTION%", user_mention_markdown)
