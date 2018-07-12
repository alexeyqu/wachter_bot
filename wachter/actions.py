import json
import logging
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
from model import Chat, User, session_scope
from constants import Actions
import constants

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def on_error(bot, update, error):
    logger.warning(f'Update "{update}" caused error "{error}"')


def authorize_user(bot, chat_id, user_id):
    status = bot.get_chat_member(chat_id, user_id).status
    return status in ['creator', 'administrator']


def on_help_command(bot, update):
    update.message.reply_text(constants.help_message)


def on_new_chat_member(bot, update, job_queue):
    chat_id = update.message.chat_id
    user_id = update.message.new_chat_members[-1].id

    for job in job_queue.jobs():
        if job.context['user_id'] == user_id and job.context['chat_id'] == chat_id and job.enabled == True:
            job.enabled = False
            job.schedule_removal()

    with session_scope() as sess:
        user = sess.query(User).filter(User.chat_id == chat_id, User.user_id == user_id).first()
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
    user = bot.get_chat_member(
        job.context['chat_id'], job.context['user_id']).user

    with session_scope() as sess:
        chat = sess.query(Chat).filter(Chat.id == chat_id).first()

    mention_markdown = user.mention_markdown()
    bot.send_message(job.context['chat_id'],
                     text=chat.notify_message,
                     parse_mode=telegram.ParseMode.MARKDOWN)


def on_kick_timeout(bot, job):
    try:
        bot.kick_chat_member(job.context['chat_id'],
                             job.context["user_id"],
                             until_date=datetime.now() + timedelta(seconds=30))
    except:
        bot.send_message(
            job.context['chat_id'], text=constants.on_failed_kick_response)


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
            user = User(chat_id=chat_id, user_id=user_id,
                        whois=update.message.text)
            sess.merge(user)

        removed = False
        for job in job_queue.jobs():
            if job.context['user_id'] == user_id and job.context['chat_id'] == chat_id and job.enabled == True:
                job.enabled = False
                job.schedule_removal()
                removed = True

        if removed:
            update.message.reply_text(message)


def on_start_command(bot, update, user_data):
    user_id = update.message.chat_id

    if user_id < 0:
        return

    with session_scope() as sess:
        users = sess.query(User).filter(User.user_id == user_id)
        user_chats = [{"title": bot.get_chat(x.chat_id).title or x.chat_id, "id": x.chat_id}
                      for x in users]

    if len(user_chats) == 0:
        update.message.reply_text('У вас нет доступных чатов.')
        return

    keyboard = [[InlineKeyboardButton(chat['title'],
                                      callback_data=json.dumps({'chat_id': chat['id'], 'action': Actions.select_chat}))]
                for chat in user_chats if authorize_user(bot, chat['id'], user_id)]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(constants.on_start_command, reply_markup=reply_markup)


def on_button_click(bot, update, user_data):
    query = update.callback_query
    data = json.loads(query.data)

    if data['action'] == Actions.select_chat:
        selected_chat_id = data['chat_id']
        keyboard = [
            [InlineKeyboardButton('Изменить таймаут кика', callback_data=json.dumps(
                {'chat_id': selected_chat_id, 'action': Actions.set_kick_timeout}))],
            [InlineKeyboardButton('Изменить сообщение при входе в чат', callback_data=json.dumps(
                {'chat_id': selected_chat_id, 'action': Actions.set_on_new_chat_member_message_response}))],
            [InlineKeyboardButton('Изменить сообщение при перезаходе в чат', callback_data=json.dumps(
                {'chat_id': selected_chat_id, 'action': Actions.set_on_known_new_chat_member_message_response}))],
            [InlineKeyboardButton('Изменить сообщение после успешного представления', callback_data=json.dumps(
                {'chat_id': selected_chat_id, 'action': Actions.set_on_successful_introducion_response}))],
            [InlineKeyboardButton('Изменить сообщение напоминания', callback_data=json.dumps(
                {'chat_id': selected_chat_id, 'action': Actions.set_notify_message}))],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_reply_markup(reply_markup=reply_markup,
                                      chat_id=query.message.chat_id,
                                      message_id=query.message.message_id)

    elif data['action'] in [Actions.set_on_new_chat_member_message_response,
                            Actions.set_kick_timeout,
                            Actions.set_notify_message,
                            Actions.set_on_known_new_chat_member_message_response,
                            Actions.set_on_successful_introducion_response]:
        bot.edit_message_text(text="Отправьте новое значение",
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id)
        user_data["chat_id"] = data['chat_id']
        user_data['action'] = data['action']


def on_message(bot, update, user_data):
    chat_id = user_data["chat_id"]
    action = user_data.get('action')

    if action is None:
        return

    if action == Actions.set_kick_timeout:
        message = update.message.text
        try:
            timeout = int(message)
            assert timeout >= 0
        except:
            update.message.reply_text(
                constants.on_failed_set_kick_timeout_response)
            return

        with session_scope() as sess:
            chat = Chat(id=chat_id, kick_timeout=timeout)
            sess.merge(chat)
        user_data['action'] = None
        update.message.reply_text(constants.on_success_set_kick_timeout_response)

    else:
        message = update.message.text_markdown
        with session_scope() as sess:
            if action == Actions.set_on_new_chat_member_message_response:
                chat = Chat(id=chat_id, on_new_chat_member_message=message)
            if action == Actions.set_on_known_new_chat_member_message_response:
                chat = Chat(id=chat_id, on_known_new_chat_member_message=message)
            if action == Actions.set_on_successful_introducion_response:
                chat = Chat(id=chat_id, on_introduce_message=message)
            if action == Actions.set_notify_message:
                chat = Chat(id=chat_id, notify_message=message)
            sess.merge(chat)

        user_data['action'] = None
        update.message.reply_text(text=constants.on_set_new_message, parse_mode=telegram.ParseMode.MARKDOWN)


def on_whois_command(bot, update, args):
    if len(args) != 1:
        update.message.reply_text("Usage: /whois <user_id>")

    chat_id = update.message.chat_id
    user_id = args[0]  # TODO: Use username instead of user_id

    with session_scope() as sess:
        user = sess.query(User).filter(User.chat_id == chat_id, User.user_id == user_id).first()

        if user is None:
            update.message.reply_text('user not found')
            return

        update.message.reply_text(f'whois: {user.whois}')
