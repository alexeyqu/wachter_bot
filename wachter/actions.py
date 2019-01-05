import json
import logging
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
from model import Chat, User, session_scope, orm_to_dict
from constants import Actions, RH_kick_messages, RH_CHAT_ID
import constants
import re
import random

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def on_error(bot, update, error):
    logger.warning(f'Update "{update}" caused error "{error}"')


def authorize_user(bot, chat_id, user_id):
    status = bot.get_chat_member(chat_id, user_id).status
    return status in ['creator', 'administrator']


def mention_markdown(bot, chat_id, user_id, message):
    user = bot.get_chat_member(chat_id, user_id).user
    if not user.name:
        # если пользователь удален, у него пропадает имя и markdown выглядит так: (tg://user?id=666)
        user_mention_markdown = ""
    else:
        user_mention_markdown = user.mention_markdown()

    # \ нужны из-за формата сообщений в маркдауне
    return message.replace('%USER\_MENTION%', user_mention_markdown)


def on_help_command(bot, update):
    update.message.reply_text(constants.help_message)


def on_skip_command(bot, update, job_queue):
    chat_id = update.message.chat_id

    if chat_id > 0:
        return

    if not update.message:
        update.message = update.edited_message

    if update.message.reply_to_message is not None:
        user_id = update.message.reply_to_message.from_user.id

        if not authorize_user(bot, chat_id, user_id):
            return
        removed = False
        for job in job_queue.jobs():
            if job.context['user_id'] == user_id and job.context['chat_id'] == chat_id and job.enabled == True:
                try:
                    bot.delete_message(
                        job.context['chat_id'], job.context['message_id'])
                except:
                    pass
                job.enabled = False
                job.schedule_removal()
                removed = True
        if removed:
            update.message.reply_text(constants.on_success_skip)
    else:
        update.message.reply_text(constants.on_failed_skip)


def on_new_chat_member(bot, update, job_queue):
    chat_id = update.message.chat_id
    user_id = update.message.new_chat_members[-1].id

    for job in job_queue.jobs():
        if job.context['user_id'] == user_id and job.context['chat_id'] == chat_id and job.enabled == True:
            job.enabled = False
            job.schedule_removal()

    with session_scope() as sess:
        user = sess.query(User).filter(
            User.chat_id == chat_id, User.user_id == user_id).first()
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

    message_markdown = mention_markdown(bot, chat_id, user_id, message)
    msg = update.message.reply_text(
        message_markdown, parse_mode=telegram.ParseMode.MARKDOWN)

    if timeout != 0:
        if timeout >= 10:
            job = job_queue.run_once(on_notify_timeout, (timeout - constants.notify_delta) * 60, context={
                "chat_id": chat_id,
                "user_id": user_id,
                "job_queue": job_queue
            })

        job = job_queue.run_once(on_kick_timeout, timeout * 60, context={
            "chat_id": chat_id,
            "user_id": user_id,
            "message_id": msg.message_id
        })


def on_notify_timeout(bot, job):
    with session_scope() as sess:
        chat = sess.query(Chat).filter(
            Chat.id == job.context['chat_id']).first()

        message_markdown = mention_markdown(
            bot, job.context['chat_id'], job.context['user_id'], chat.notify_message)

        message = bot.send_message(job.context['chat_id'],
                                   text=message_markdown,
                                   parse_mode=telegram.ParseMode.MARKDOWN)

        job.context['job_queue'].run_once(delete_message, constants.notify_delta * 60, context={
            "chat_id": job.context['chat_id'],
            "user_id": job.context['user_id'],
            "message_id": message.message_id
        })


def delete_message(bot, job):
    try:
        bot.delete_message(job.context['chat_id'], job.context['message_id'])
    except:
        print(f"can't delete {job.context['message_id']} from {job.context['chat_id']}")


def on_kick_timeout(bot, job):
    try:
        bot.delete_message(
            job.context['chat_id'], job.context['message_id'])
    except:
        pass

    try:
        bot.kick_chat_member(job.context['chat_id'],
                             job.context["user_id"],
                             until_date=datetime.now() + timedelta(seconds=60))

        with session_scope() as sess:
            chat = sess.query(Chat).filter(
                Chat.id == job.context['chat_id']).first()
            message_markdown = mention_markdown(
                bot, job.context['chat_id'], job.context['user_id'], chat.on_kick_message)

        if (job.context['chat_id'] == RH_CHAT_ID):
            message_markdown = mention_markdown(
                bot, job.context['chat_id'], job.context['user_id'], random.choice(RH_kick_messages))
            bot.send_message(job.context['chat_id'],
                            text=message_markdown,
                            parse_mode=telegram.ParseMode.MARKDOWN)    
        else:
            bot.send_message(job.context['chat_id'],
                            text=message_markdown,
                            parse_mode=telegram.ParseMode.MARKDOWN)
    except Exception as e:
        logging.error(e)
        bot.send_message(job.context['chat_id'],
                         text=constants.on_failed_kick_response)


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
                try:
                    bot.delete_message(
                        job.context['chat_id'], job.context['message_id'])
                except:
                    pass
                job.enabled = False
                job.schedule_removal()
                removed = True

        if removed:
            message_markdown = mention_markdown(bot, chat_id, user_id, message)
            update.message.reply_text(
                message_markdown, parse_mode=telegram.ParseMode.MARKDOWN)

    else:
        on_message(bot, update, user_data={}, job_queue=job_queue)


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
    update.message.reply_text(
        constants.on_start_command, reply_markup=reply_markup)


def on_button_click(bot, update, user_data):
    query = update.callback_query
    data = json.loads(query.data)

    if data['action'] == Actions.start_select_chat:
        with session_scope() as sess:
            user_id = query.from_user.id
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
        bot.edit_message_reply_markup(reply_markup=reply_markup,
                                      chat_id=query.message.chat_id,
                                      message_id=query.message.message_id)

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
            [InlineKeyboardButton('Изменить сообщение после кика', callback_data=json.dumps(
                {'chat_id': selected_chat_id, 'action': Actions.set_on_kick_message}))],
            [InlineKeyboardButton('Изменить regex для фильтра сообщений', callback_data=json.dumps(
                {'chat_id': selected_chat_id, 'action': Actions.set_regex_filter}))],
            [InlineKeyboardButton("Изменить фильтрацию только для новых пользователей", callback_data=json.dumps(
                {'chat_id': selected_chat_id, 'action': Actions.set_filter_only_new_users}
            ))],
            [InlineKeyboardButton('Получить текущие настройки', callback_data=json.dumps(
                {'chat_id': selected_chat_id, 'action': Actions.get_current_settings}))]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_reply_markup(reply_markup=reply_markup,
                                      chat_id=query.message.chat_id,
                                      message_id=query.message.message_id)

    elif data['action'] in [Actions.set_on_new_chat_member_message_response,
                            Actions.set_kick_timeout,
                            Actions.set_notify_message,
                            Actions.set_on_known_new_chat_member_message_response,
                            Actions.set_on_successful_introducion_response,
                            Actions.set_on_kick_message,
                            Actions.set_regex_filter,
                            Actions.set_filter_only_new_users]:
        bot.edit_message_text(text="Отправьте новое значение",
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id)
        user_data["chat_id"] = data['chat_id']
        user_data['action'] = data['action']

    elif data['action'] == Actions.get_current_settings:
        keyboard = [
            [InlineKeyboardButton('К настройке чата', callback_data=json.dumps(
                {'chat_id': data['chat_id'], 'action': Actions.select_chat})),
             InlineKeyboardButton('К списку чатов', callback_data=json.dumps(
                 {'action': Actions.start_select_chat}))],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        with session_scope() as sess:
            chat = sess.query(Chat).filter(Chat.id == data['chat_id']).first()
            bot.edit_message_text(text=constants.get_settings_message.format(**chat.__dict__),
                                  parse_mode=telegram.ParseMode.MARKDOWN,
                                  chat_id=query.message.chat_id,
                                  message_id=query.message.message_id,
                                  reply_markup=reply_markup)

        user_data['action'] = None


def filter_message(chat_id, message):
    with session_scope() as sess:
        chat = sess.query(Chat).filter(Chat.id == chat_id).first()

        if chat.regex_filter is None:
            return False
        else:
            return re.search(chat.regex_filter, message)



def on_forward(bot, update, job_queue):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    removed = False

    if chat_id < 0 and not authorize_user(bot, chat_id, user_id):
        with session_scope() as sess:
            chat = sess.query(Chat).filter(
                Chat.id == chat_id == chat_id).first()
            if chat.regex_filter is None:
                return

        for job in job_queue.jobs():
            if job.context['user_id'] == user_id and job.context['chat_id'] == chat_id and job.enabled == True:
                removed = True
                try:
                    bot.delete_message(
                        job.context['chat_id'], job.context['message_id'])
                except:
                    pass
                job.enabled = False
                job.schedule_removal()

        if removed:
            bot.delete_message(chat_id, update.message.message_id)
            message_markdown = mention_markdown(
                bot, chat_id, user_id, constants.on_filtered_message)
            message = bot.send_message(chat_id,
                                       text=message_markdown,
                                       parse_mode=telegram.ParseMode.MARKDOWN)
            bot.kick_chat_member(chat_id, user_id, until_date=datetime.now() + timedelta(seconds=60))


def is_new_user(chat_id, user_id):
    with session_scope() as sess:
        #  if user is not in database he hasn't introduced himself with #whois
        user = sess.query(User).filter(User.user_id == user_id, User.chat_id == chat_id).first()
        is_new = not user
        return is_new


def is_chat_filters_new_users(chat_id):
    with session_scope() as sess:
        filter_only_new_users = sess.query(Chat.filter_only_new_users).filter(Chat.id == chat_id).first()
        return filter_only_new_users


def on_message(bot, update, user_data, job_queue):
    chat_id = update.message.chat_id

    if chat_id < 0:
        user_id = update.message.from_user.id
        if update.message.forward_from:
            on_forward(bot, update, job_queue)
            return

        message_text = update.message.text or update.message.caption
        filter_mask = not authorize_user(bot, chat_id, user_id) and filter_message(chat_id, message_text)
        
        if is_chat_filters_new_users(chat_id):
            filter_mask = filter_mask and is_new_user(chat_id, user_id)

        if filter_mask:
            bot.delete_message(chat_id, update.message.message_id)
            message_markdown = mention_markdown(
                bot, chat_id, user_id, constants.on_filtered_message)
            for job in job_queue.jobs():
                if job.context['user_id'] == user_id and job.context['chat_id'] == chat_id and job.enabled == True:
                    try:
                        bot.delete_message(
                            job.context['chat_id'], job.context['message_id'])
                    except:
                        pass
                    job.enabled = False
                    job.schedule_removal()
            message = bot.send_message(chat_id,
                                       text=message_markdown,
                                       parse_mode=telegram.ParseMode.MARKDOWN)
            bot.kick_chat_member(chat_id, user_id, until_date=datetime.now() + timedelta(seconds=60))

    user_id = chat_id
    action = user_data.get('action')

    if action is None:
        return

    chat_id = user_data["chat_id"]

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

        keyboard = [
            [InlineKeyboardButton('К настройке чата', callback_data=json.dumps(
                {'chat_id': chat_id, 'action': Actions.select_chat})),
             InlineKeyboardButton('К списку чатов', callback_data=json.dumps(
                 {'action': Actions.start_select_chat}))],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            constants.on_success_set_kick_timeout_response, reply_markup=reply_markup)

    elif action in [Actions.set_on_new_chat_member_message_response,
                    Actions.set_notify_message,
                    Actions.set_on_known_new_chat_member_message_response,
                    Actions.set_on_successful_introducion_response,
                    Actions.set_on_kick_message,
                    Actions.set_regex_filter,
                    Actions.set_filter_only_new_users]:
        message = update.message.text_markdown
        with session_scope() as sess:
            if action == Actions.set_on_new_chat_member_message_response:
                chat = Chat(id=chat_id, on_new_chat_member_message=message)
            if action == Actions.set_on_known_new_chat_member_message_response:
                chat = Chat(
                    id=chat_id, on_known_new_chat_member_message=message)
            if action == Actions.set_on_successful_introducion_response:
                chat = Chat(id=chat_id, on_introduce_message=message)
            if action == Actions.set_notify_message:
                chat = Chat(id=chat_id, notify_message=message)
            if action == Actions.set_on_kick_message:
                chat = Chat(id=chat_id, on_kick_message=message)
            if action == Actions.set_filter_only_new_users:
                if message.lower() in ["true", "1"]:
                    filter_only_new_users = True
                else:
                    filter_only_new_users = False
                chat = Chat(id=chat_id, filter_only_new_users=filter_only_new_users)

            if action == Actions.set_regex_filter:
                if message == "%TURN_OFF%":
                    chat = Chat(id=chat_id, regex_filter=None)
                else:
                    message = update.message.text
                    chat = Chat(id=chat_id, regex_filter=message)
            sess.merge(chat)

        user_data['action'] = None

        keyboard = [
            [InlineKeyboardButton('К настройке чата', callback_data=json.dumps(
                {'chat_id': chat_id, 'action': Actions.select_chat})),
             InlineKeyboardButton('К списку чатов', callback_data=json.dumps(
                 {'action': Actions.start_select_chat}))],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            constants.on_set_new_message, reply_markup=reply_markup)


def on_whois_command(bot, update, args):
    if len(args) != 1:
        update.message.reply_text("Usage: /whois <user_id>")

    chat_id = update.message.chat_id
    user_id = args[0]  # TODO: Use username instead of user_id

    with session_scope() as sess:
        user = sess.query(User).filter(
            User.chat_id == chat_id, User.user_id == user_id).first()

        if user is None:
            update.message.reply_text('user not found')
            return

        update.message.reply_text(f'whois: {user.whois}')
