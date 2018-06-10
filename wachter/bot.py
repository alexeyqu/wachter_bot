from telegram.ext import Updater, CommandHandler, Filters, MessageHandler
import telegram
import logging
from model import Chat, User, session_scope
import default_messages
from datetime import datetime, timedelta
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

def on_error(bot, update, error):
    logger.warning(f'Update "{update}" caused error "{error}"')


def authorize_user(bot, update):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    status = bot.get_chat_member(chat_id, user_id).status
    return status in ['creator', 'administrator']

def on_help_command(bot, update):
    update.message.reply_text(default_messages.help_message)

def on_set_new_chat_member_message(bot, update, args):
    chat_id = update.message.chat_id
    message = " ".join(args)

    if not authorize_user(bot, update):
        # update.message.reply_text(default_messages.on_failed_auth_response)
        return

    if message == '':
        update.message.reply_text(default_messages.on_empty_message)
        return

    with session_scope() as sess:
        chat = Chat(id=chat_id, on_new_chat_member_message=message)
        sess.merge(chat)

    update.message.reply_text(
        default_messages.on_set_new_chat_member_message_response)


def on_set_introduce_message(bot, update, args):
    chat_id = update.message.chat_id
    message = " ".join(args)

    if not authorize_user(bot, update):
        return

    if message == '':
        update.message.reply_text(default_messages.on_empty_message)
        return

    with session_scope() as sess:
        chat = Chat(id=chat_id, on_introduce_message=message)
        sess.merge(chat)

    update.message.reply_text(
        default_messages.on_set_introduce_message_response)


def on_set_kick_timeout(bot, update, args):
    chat_id = update.message.chat_id

    if not authorize_user(bot, update):
        return

    try:
        timeout = int(args[0])
        assert timeout >= 0
    except:
        update.message.reply_text(
            default_messages.on_failed_set_kick_timeout_response)
        return

    with session_scope() as sess:
        chat = Chat(id=chat_id, kick_timeout=timeout)
        sess.merge(chat)

    update.message.reply_text(
        default_messages.on_success_set_kick_timeout_response)


def on_new_chat_member(bot, update, job_queue):
    chat_id = update.message.chat_id
    user_id = update.message.new_chat_members[-1].id

    for job in job_queue.jobs():
        if job.context['user_id'] == user_id and job.context['chat_id'] == chat_id and job.enabled == True:
            job.enabled = False
            job.schedule_removal()

    with session_scope() as sess:
        user = sess.query(User).filter(User.chat_id == chat_id, User.user_id == user_id).first()

        if user is not None:
            update.message.reply_text('welcome back')
            return

    with session_scope() as sess:
        chat = sess.query(Chat).filter(Chat.id == chat_id).first()

        if chat is None:
            chat = Chat(id=chat_id)
            sess.add(chat)
            sess.commit()

        message = chat.on_new_chat_member_message
        timeout = chat.kick_timeout

    if timeout != 0:
        if timeout >= 10:
            job = job_queue.run_once(on_notify_timeout, (timeout - 9) * 60, context={
                "chat_id": chat_id,
                "user_id": user_id
            })

        job = job_queue.run_once(on_kick_timeout, timeout * 60, context={
            "chat_id": chat_id,
            "user_id": user_id
        })

    update.message.reply_text(message)


def on_notify_timeout(bot, job):
    user = bot.get_chat_member(job.context['chat_id'], job.context['user_id']).user

    mention_markdown = user.mention_markdown()
    bot.send_message(job.context['chat_id'],
                     text=f'ping {mention_markdown}',
                     parse_mode=telegram.ParseMode.MARKDOWN)



def on_kick_timeout(bot, job):
    try:
        bot.kick_chat_member(job.context['chat_id'],
                             job.context["user_id"],
                             until_date=datetime.now() + timedelta(seconds=30))
    except:
        bot.send_message(
            job.context['chat_id'], text=default_messages.on_failed_kick_response)


def on_successful_introduce(bot, update, job_queue):
    if not update.message:
        update.message = update.edited_message

    if "#whois" in update.message.parse_entities(types=['hashtag']).values():
        chat_id = update.message.chat_id
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
        for job in job_queue.jobs():
            if job.context['user_id'] == user_id and job.context['chat_id'] == chat_id and job.enabled == True:
                job.enabled = False
                job.schedule_removal()
                removed = True

        if removed:
            update.message.reply_text(message)


def main():
    updater = Updater(os.environ['TELEGRAM_TOKEN'])
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("set_new_chat_member_message", on_set_new_chat_member_message,
                                  pass_args=True))

    dp.add_handler(CommandHandler("set_introduce_message", on_set_introduce_message,
                                  pass_args=True))

    dp.add_handler(CommandHandler("set_kick_timeout", on_set_kick_timeout,
                                  pass_args=True))

    dp.add_handler(CommandHandler("wachter_help", on_help_command))

    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, on_new_chat_member,
                                  pass_job_queue=True))

    dp.add_handler(MessageHandler(Filters.entity('hashtag'), on_successful_introduce,
                                  pass_job_queue=True, edited_updates=True))

    dp.add_error_handler(on_error)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
