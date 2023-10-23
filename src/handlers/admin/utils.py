import json
from telegram import Bot, InlineKeyboardButton
from telegram.ext import CallbackContext

from src.model import User, session_scope
from src import constants


def authorize_user(bot: Bot, chat_id: int, user_id: int):
    try:
        status = bot.get_chat_member(chat_id, user_id).status
        return status in ["creator", "administrator"]
    except Exception:
        return False


def get_chats_list(user_id, context: CallbackContext):
    with session_scope() as sess:
        users = sess.query(User).filter(User.user_id == user_id).all()
    return _get_chats_helper(users, user_id, context.bot)


def _get_chats_helper(users: list, user_id: int, bot: Bot):
    for x in users:
        try:
            if authorize_user(bot, x.chat_id, user_id):
                yield {
                    "title": bot.get_chat(x.chat_id).title or x.chat_id,
                    "id": x.chat_id,
                }
        except Exception:
            pass


def create_chats_list_keyboard(user_chats, context: CallbackContext, user_id):
    return [
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
