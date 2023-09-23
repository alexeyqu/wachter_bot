from telegram import Update
from telegram.ext import CallbackContext

from src import constants

def help_handler(update: Update, _: CallbackContext):
    update.message.reply_text(constants.help_message)
