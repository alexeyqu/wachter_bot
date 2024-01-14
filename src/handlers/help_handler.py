from telegram import Update
from telegram.ext import CallbackContext

from src.texts import _


def help_handler(update: Update, _context: CallbackContext):
    update.message.reply_text(_("msg__help"))
