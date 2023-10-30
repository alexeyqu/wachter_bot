from functools import wraps

from telegram import Update
from telegram.ext import CallbackContext

from src.constants import DEBUG, TEAM_TELEGRAM_IDS


def admin(func):
    """
    A decorator to ensure that a particular function is only executed in private chats,
    and not in group chats.

    Args:
    func (Callable): The function to be wrapped by the decorator.

    Returns:
    Callable: The wrapper function which includes the functionality for checking the chat type.
    """

    @wraps(func)
    def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        if update.message.chat_id < 0:
            return  # Skip the execution of the function in case of group chat
        return func(update, context, *args, **kwargs)

    return wrapper

def debug(func):
    """
    A decorator to ensure that a particular function is only executed for debug purposes, i.e. by someone from the team.

    Args:
    func (Callable): The function to be wrapped by the decorator.

    Returns:
    Callable: The wrapper function which includes the functionality for checking the called ID.
    """

    @wraps(func)
    def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        if DEBUG or update.message.chat_id in TEAM_TELEGRAM_IDS:
            return func(update, context, *args, **kwargs)

    return wrapper
