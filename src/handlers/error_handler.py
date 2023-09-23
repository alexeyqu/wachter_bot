import logging

from telegram import Update
from telegram.ext import CallbackContext

# todo use telegram logger here
logger = logging.getLogger(__name__)


def error_handler(update: Update, context: CallbackContext):
    logger.warning(f'Update "{update}" caused error "{context.error}"')
