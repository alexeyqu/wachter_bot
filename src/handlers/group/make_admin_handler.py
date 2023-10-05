import logging
from telegram import ChatMember, Update
from telegram.ext import CallbackContext

from src import constants


logger = logging.getLogger(__name__)


def on_make_admin_handler(update: Update, context: CallbackContext):
    status_change = update.my_chat_member.difference().get("status")
    if status_change is None:
        return None

    old_status, new_status = status_change
    if new_status == ChatMember.ADMINISTRATOR and old_status != ChatMember.ADMINISTRATOR:
        context.bot.send_message(update.effective_chat.id, constants.on_make_admin_message)
