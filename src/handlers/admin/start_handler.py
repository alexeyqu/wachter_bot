import json
import logging
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
from typing import List

from src import constants
from src.model import Chat, session_scope

from .utils import authorize_user


logger = logging.getLogger(__name__)

# todo @admin decorator to prevent / tweak behaviour when calling from group chats
# this will be a nice replacement for "if user_id < 0" checks
def start_handler(update: Update, context: CallbackContext):
    # TODO replace with update.message.from_user.id when we have @admin decorator
    user_id = update.message.chat_id

    if user_id < 0:
        return

    with session_scope() as sess:
        # TODO slow, need to rethink the DB schema to get all user's chats efficiently without the whois requirement
        # nullable whois field? would that cause problems?
        chats = sess.query(Chat).all()
        user_chats = _filter_chats(chats, user_id, context.bot)

    if len(user_chats) == 0:
        update.message.reply_text("У вас нет доступных чатов.")
        return

    keyboard = [
        [
            InlineKeyboardButton(
                chat["title"],
                callback_data=json.dumps(
                    {"chat_id": chat["id"], "action": constants.Actions.select_chat}
                ),
            )
        ]
        for chat in user_chats
        if authorize_user(context.bot, chat["id"], user_id)
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(constants.on_start_command, reply_markup=reply_markup)


def _filter_chats(chats: List[Chat], user_id: int, bot: Bot) -> List[Chat]:
    filtered_chats = []
    for chat in chats:
        try:
            if authorize_user(bot, chat.id, user_id):
                filtered_chats.append({
                    "title": bot.get_chat(chat.id).title or chat.id,
                    "id": chat.id,
                })
        except Exception as e:
            logger.error(e)
    return filtered_chats
