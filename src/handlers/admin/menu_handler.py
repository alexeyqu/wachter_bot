import json
from typing import Union, Iterator, Dict

from telegram import InlineKeyboardMarkup, ParseMode, Update, Bot
from telegram.ext import CallbackContext
from datetime import datetime, timedelta

from src import constants
from src.model import Chat, User, session_scope

from src.handlers.group.group_handler import on_kick_timeout, on_notify_timeout
from src.utils.button import Button

from .utils import authorize_user, new_button, create_keyboard, admin

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Some message about what the code is doing.")


def _get_chats(
    users: list, user_id: int, bot: Bot
) -> Iterator[Dict[str, Union[str, int]]]:
    for x in users:
        try:
            if authorize_user(bot, x.chat_id, user_id):
                yield {
                    "title": bot.get_chat(x.chat_id).title or x.chat_id,
                    "id": x.chat_id,
                }
        except Exception:
            pass


# @admin
def handle_chats_list(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    with session_scope() as sess:
        users = sess.query(User).filter(User.user_id == user_id)
        user_chats = list(_get_chats(users, user_id, context.bot))

    if len(user_chats) == 0:
        update.message.reply_text("У вас нет доступных чатов.")
        return
    buttons = []
    for chat in user_chats:
        buttons.append(new_button(Button.SELECT_CHAT, chat.get("id")))
    keyboard = create_keyboard(buttons)
    update.message.reply_text(constants.on_start_command, reply_markup=keyboard)


def update_reply_markup(context, keyboard, query):
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.edit_message_reply_markup(
        reply_markup=reply_markup,
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
    )


def callback_action(data, query, context):
    context.bot.edit_message_text(
        text="Отправьте новое значение",
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
    )
    context.user_data.update({"chat_id": data["chat_id"], "action": data["action"]})


def callback_get_current_settings(data, query, context):
    keyboard = [
        [
            new_button(
                Button.SELECT_CHAT, data["chat_id"], constants.Actions.select_chat
            ),
            new_button(
                "К списку чатов", data["chat_id"], constants.Actions.start_select_chat
            ),
        ]
    ]
    with session_scope() as sess:
        chat = sess.query(Chat).filter(Chat.id == data["chat_id"]).first()
        context.bot.edit_message_text(
            text=constants.get_settings_message.format(**chat.__dict__),
            parse_mode=ParseMode.MARKDOWN,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    context.user_data["action"] = None


def set_chat_attribute(chat_id, attribute, value):
    with session_scope() as sess:
        chat = Chat(id=chat_id, **{attribute: value})
        sess.merge(chat)


def handle_set_kick_settings(update: Update, context: CallbackContext):
    buttons = [
        new_button(Button.SET_KICK_TIMEOUT, context.user_data["chat_id"]),
        new_button(Button.KICK_IF_NO_INTRO, context.user_data["chat_id"]),
        new_button(Button.SET_AFTER_KICK_MESSAGE, context.user_data["chat_id"]),
        new_button(Button.SEE_CURRENT_KICK_SETTINGS, context.user_data["chat_id"]),
        new_button(Button.Button.BACK_TO_SETTINGS, context.user_data["chat_id"]),
    ]
    keyboard = create_keyboard(buttons)
    update.message.reply_text(reply_markup=keyboard)


def handle_settings(update: Update, context: CallbackContext):
    buttons = [
        new_button(Button.SET_KICK_SETTINGS, context.user_data["chat_id"]),
        new_button(Button.SET_INTRO_SETTINGS, context.user_data["chat_id"]),
    ]
    keyboard = create_keyboard(buttons)
    update.message.reply_text(reply_markup=keyboard)


def handle_back(update: Update, context: CallbackContext):
    pass


def handle_set_kick_timeout(
    update: Update, context: CallbackContext, user_chat_id: int
):
    message = update.message.text
    try:
        timeout = int(message)
        assert timeout >= 0
    except:
        update.message.reply_text(constants.on_failed_set_kick_timeout_response)
        return

    set_chat_attribute(user_chat_id, "kick_timeout", timeout)
    for job in context.job_queue.jobs():
        if job.name in [on_kick_timeout.__name__, on_notify_timeout.__name__]:
            job_context = job.context
            job_creation_time = datetime.fromtimestamp(job_context.get("creation_time"))
            new_timeout = job_creation_time + timedelta(seconds=timeout * 60)
            if job.name == on_kick_timeout.__name__:
                if new_timeout < datetime.now():
                    new_timeout = 0
                next_job_func = on_kick_timeout
            else:
                new_timeout = new_timeout - timedelta(
                    seconds=constants.notify_delta * 60
                )
                next_job_func = on_notify_timeout

            job.schedule_removal()
            job_context["timeout"] = new_timeout
            job = context.job_queue.run_once(
                next_job_func, new_timeout, context=job_context
            )

    context.user_data["action"] = None
    # send_message_with_keyboard(update, constants.on_success_set_kick_timeout_response, user_chat_id)


def handle_intro_settings(update: Update, context: CallbackContext):
    buttons = [
        new_button(Button.SEE_CURRENT_INTRO_SETTINGS, context.user_data["chat_id"]),
        new_button(Button.SET_WELCOME_MESSAGE, context.user_data["chat_id"]),
        new_button(Button.SET_WHOIS_LENGTH, context.user_data["chat_id"]),
        new_button(Button.SET_REWELCOME_MESSAGE, context.user_data["chat_id"]),
        new_button(Button.SET_WARNING_MESSAGE, context.user_data["chat_id"]),
        new_button(Button.SET_THX_MESSAGE, context.user_data["chat_id"]),
    ]
    keyboard = create_keyboard(buttons)
    update.message.reply_text(reply_markup=keyboard)


def handle_current_intro_settings(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    keyboard = create_keyboard(
        new_button(Button.BACK_TO_INTRO_SETTINGS, context.user_data["chat_id"])
    )
    with session_scope() as sess:
        chat = sess.query(Chat).filter(Chat.id == data["chat_id"]).first()
        context.bot.edit_message_text(
            text=constants.get_settings_message.format(**chat.__dict__),
            parse_mode=ParseMode.MARKDOWN,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            reply_markup=keyboard,
        )


def handle_set_warning_message(update: Update, context: CallbackContext):
    keyboard = create_keyboard(
        new_button(Button.BACK_TO_INTRO_SETTINGS, context.user_data["chat_id"])
    )
    message = update.message.text
    constants.get_settings_message.format(notify_message=message)
    update.message.reply_text(constants.on_set_new_message, reply_markup=keyboard)


def handle_set_warning_time(update: Update, context: CallbackContext):
    keyboard = create_keyboard(
        new_button(Button.BACK_TO_INTRO_SETTINGS, context.user_data["chat_id"])
    )
    message = update.message.text
    constants.get_settings_message.format(notify_message=message)
    update.message.reply_text(constants.on_set_new_message, reply_markup=keyboard)


def handle_set_thx_message(update: Update, context: CallbackContext):
    keyboard = create_keyboard(
        new_button(Button.BACK_TO_INTRO_SETTINGS, context.user_data["chat_id"])
    )
    message = update.message.text
    constants.get_settings_message.format(on_introduce_message=message)
    update.message.reply_text(constants.on_set_new_message, reply_markup=keyboard)


def handle_whois_length(update: Update, context: CallbackContext):
    keyboard = create_keyboard(
        new_button(Button.BACK_TO_INTRO_SETTINGS, context.user_data["chat_id"])
    )
    message = int(update.message.text)
    constants.min_whois_length = message
    update.message.reply_text(
        constants.on_success_set_kick_timeout_response, reply_markup=keyboard
    )


def handle_set_welcome_message(update: Update, context: CallbackContext):
    keyboard = create_keyboard(
        new_button(Button.BACK_TO_INTRO_SETTINGS, context.user_data["chat_id"])
    )
    message = update.message.text
    constants.get_settings_message.format(on_new_chat_member_message=message)
    update.message.reply_text(constants.on_set_new_message, reply_markup=keyboard)


def handle_set_rewelcome_message(update: Update, context: CallbackContext):
    keyboard = create_keyboard(
        new_button(Button.BACK_TO_INTRO_SETTINGS, context.user_data["chat_id"])
    )
    message = update.message.text
    constants.get_settings_message.format(on_known_new_chat_member_message=message)
    update.message.reply_text(constants.on_set_new_message, reply_markup=keyboard)


def handle_after_kick_message(update: Update, context: CallbackContext):
    keyboard = create_keyboard(
        new_button(Button.BACK_TO_INTRO_SETTINGS, context.user_data["chat_id"])
    )
    message = update.message.text
    constants.get_settings_message.format(on_kick_message=message)
    update.message.reply_text(constants.on_set_new_message, reply_markup=keyboard)
