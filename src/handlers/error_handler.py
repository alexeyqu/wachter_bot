from telegram import Update
from telegram.ext import CallbackContext
from sentry_sdk import capture_exception

from src.logging import tg_logger


def error_handler(update: Update, context: CallbackContext):
    capture_exception(context.error)
    tg_logger.warning(f'Update "{update}" caused error', exc_info=context.error)
