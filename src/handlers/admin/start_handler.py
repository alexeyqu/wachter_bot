import json
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from src import constants
from src.model import User, session_scope

from .utils import authorize_user, get_chats_list, create_chats_list_keyboard


# todo @admin decorator to prevent / tweak behaviour when calling from group chats
# this will be a nice replacement for "if user_id < 0" checks
def start_handler(update: Update, context: CallbackContext):
    user_id = update.message.chat_id

    if user_id < 0:
        return

    with session_scope() as sess:
        users = sess.query(User).filter(User.user_id == user_id)
        user_chats = list(_get_chats(users, user_id, context.bot))

    if len(user_chats) == 0:
        update.message.reply_text("У вас нет доступных чатов.")
        return

    reply_markup = InlineKeyboardMarkup(
        create_chats_list_keyboard(user_chats, context, user_id)
    )
    update.message.reply_text(constants.on_start_command, reply_markup=reply_markup)


def _get_chats(users: list, user_id: int, bot: Bot):
    for x in users:
        try:
            if authorize_user(bot, x.chat_id, user_id):
                yield {
                    "title": bot.get_chat(x.chat_id).title or x.chat_id,
                    "id": x.chat_id,
                }
        except Exception:
            pass
