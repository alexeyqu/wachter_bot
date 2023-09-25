from telegram import Bot


def authorize_user(bot: Bot, chat_id: int, user_id: int):
    try:
        status = bot.get_chat_member(chat_id, user_id).status
        return status in ["creator", "administrator"]
    except Exception:
        return False
