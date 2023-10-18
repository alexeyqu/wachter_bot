from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Union
from functools import wraps

from src.model import Chat, session_scope
from src.utils.button import Button

# from src.callbacks import actions_map, callback_map

from telegram import Bot, Update
from telegram.ext import CallbackContext

# actions_map = {**callback_map, **actions_map}


def admin(func):
    @wraps(func)
    def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        if update.message.chat_id < 0:
            return  # Skip the execution of the function in case of group chat
        return func(update, context, *args, **kwargs)


def authorize_user(bot: Bot, chat_id: int, user_id: int):
    try:
        status = bot.get_chat_member(chat_id, user_id).status
        return status in ["creator", "administrator"]
    except Exception:
        return False


def set_chat_attribute(chat_id, attribute, value):
    with session_scope() as sess:
        chat = Chat(id=chat_id, **{attribute: value})
        sess.merge(chat)


def new_button(button: Button, chat_id):
    from src.callbacks import actions_map, callback_map

    actions_map = {**callback_map, **actions_map}
    return InlineKeyboardButton(
        button.value,
        callback_data={"chat_id": chat_id, "action": actions_map.get(button)},
    )


def create_keyboard(
    buttons: Union[List[List[InlineKeyboardButton]], List[InlineKeyboardButton]]
) -> InlineKeyboardMarkup:
    """
    Create a keyboard layout.

    :param buttons: A list of InlineKeyboardButton instances or a list of lists of InlineKeyboardButton instances.
    :return: InlineKeyboardMarkup instance.
    """
    if all(isinstance(button, InlineKeyboardButton) for button in buttons):
        buttons = [[button] for button in buttons]

    return InlineKeyboardMarkup(buttons)


def send_message_with_keyboard(update, message_text, chat_id=None):
    buttons = [
        [Button.SET_KICK_SETTINGS, Button.SET_KICK_TIMEOUT],
        [Button.SELECT_CHAT, Button.CHATS_LIST],
    ]
    reply_markup = create_keyboard(buttons)
    update.message.reply_text(message_text, reply_markup=reply_markup)
