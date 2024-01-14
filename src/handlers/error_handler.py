from telegram import Update
from telegram.ext import CallbackContext

from src.logging import tg_logger


def error_handler(update: Update, context: CallbackContext):
    tg_logger.warning(f'Update "{update.message}" caused error', exc_info=context.error, extra={"update": update})
