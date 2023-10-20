from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from src import constants

from .utils import get_chats_list, create_chats_list_keyboard


# todo @admin decorator to prevent / tweak behaviour when calling from group chats
# this will be a nice replacement for "if user_id < 0" checks
def start_handler(update: Update, context: CallbackContext):
    user_id = update.message.chat_id

    if user_id < 0:
        return

    user_chats = list(get_chats_list(user_id, context))

    if len(user_chats) == 0:
        update.message.reply_text("У вас нет доступных чатов.")
        return

    reply_markup = InlineKeyboardMarkup(
        create_chats_list_keyboard(user_chats, context, user_id)
    )
    update.message.reply_text(constants.on_start_command, reply_markup=reply_markup)
