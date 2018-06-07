from telegram.ext import Updater, CommandHandler, Filters, MessageHandler
import logging
from model import Chat, session_scope
import config
from datetime import datetime, timedelta


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def authorize_user(bot, update):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    status = bot.get_chat_member(chat_id, user_id).status
    return status in ['creator', 'administrator']


def on_error(bot, update, error):
    logger.warning(f'Update "{update}" caused error "{error}"')


def on_set_new_chat_member_message(bot, update, args):
    chat_id = update.message.chat_id
    message = " ".join(args)

    with session_scope() as sess:
        chat = Chat(id=chat_id, on_new_chat_member_message=message)
        sess.merge(chat)

    update.message.reply_text(config.on_set_new_chat_member_message_response)


def on_set_introduce_message(bot, update, args):
    chat_id = update.message.chat_id
    message = " ".join(args)

    with session_scope() as sess:
        chat = Chat(id=chat_id, on_introduce_message=message)
        sess.merge(chat)

    update.message.reply_text(config.on_set_introduce_message_response)


def on_set_kick_timeout(bot, update, args):
    chat_id = update.message.chat_id

    if not authorize_user(bot, update):
        update.message.reply_text(config.on_failed_auth_response)
        return

    try:
        timeout = int(args[0])
        assert timeout >= 0
    except:
        update.message.reply_text(config.on_failed_set_kick_timeout_response)
        return

    with session_scope() as sess:
        chat = Chat(id=chat_id, kick_timeout=timeout)
        sess.merge(chat)

    update.message.reply_text(config.on_success_set_kick_timeout_response)


def on_new_chat_member(bot, update, job_queue):
    chat_id = update.message.chat_id

    with session_scope() as sess:
        chat = sess.query(Chat).filter(Chat.id == chat_id).first()

        if chat is None:
            chat = Chat(id=chat_id)
            sess.add(chat)
            sess.commit()

        message = chat.on_new_chat_member_message
        timeout = chat.kick_timeout

    if timeout != 0:
        job = job_queue.run_once(on_timeout, timeout * 60, context={
            "chat_id": chat_id,
            "user_id": update.message.new_chat_members[-1].id
        })

    update.message.reply_text(message)


def on_timeout(bot, job):
    try:
        bot.kick_chat_member(job.context['chat_id'],
                             job.context["user_id"],
                             until_date=datetime.now() + timedelta(seconds=30))
    except:
        bot.send_message(job.context['chat_id'], text=config.on_failed_kick_response)


def on_successful_introduce(bot, update, job_queue):
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

        for job in job_queue.jobs():
            if job.context['user_id'] == user_id:
                job.schedule_removal()
                update.message.reply_text(message)


def main():
    updater = Updater("610195297:AAGCT-nqdT3TDspTO2aip1-BGJ5y4Pmu4AE")
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("set_new_chat_member_message", on_set_new_chat_member_message,
                                  pass_args=True))

    dp.add_handler(CommandHandler("set_introduce_message", on_set_introduce_message,
                                  pass_args=True))

    dp.add_handler(CommandHandler("set_kick_timeout", on_set_kick_timeout,
                                  pass_args=True))

    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, on_new_chat_member,
                                  pass_job_queue=True))

    dp.add_handler(MessageHandler(Filters.entity('hashtag'), on_successful_introduce,
                                  pass_job_queue=True))

    dp.add_error_handler(on_error)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
