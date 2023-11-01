from telegram import Update
from telegram.ext import CallbackContext

from src.texts import _


def help_handler(update: Update, _: CallbackContext):
    update.message.reply_text(_("msg__help"))
