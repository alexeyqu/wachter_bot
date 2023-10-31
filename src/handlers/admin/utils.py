import json
from typing import Iterator, Dict, List

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from src.logging import tg_logger
from src.model import User, session_scope
from src import constants


def new_button(text: str, chat_id: int, action: str) -> InlineKeyboardButton:
    """
    Create a new InlineKeyboardButton with associated callback data.

    Args:
    text (str): The text to be displayed on the button.
    chat_id (int): The chat ID to be included in the callback data.
    action (str): The action to be performed, included in the callback data.

    Returns:
    InlineKeyboardButton: The created InlineKeyboardButton instance.
    """
    callback_data = json.dumps({"chat_id": chat_id, "action": action})
    return InlineKeyboardButton(text, callback_data=callback_data)


def new_keyboard_layout(
    button_configs: List[List[Dict[str, str]]], chat_id: int
) -> InlineKeyboardMarkup:
    """
    Create a new InlineKeyboardMarkup layout based on a configuration list.

    Args:
    button_configs (List[List[Dict[str, str]]]): A list of button configurations.
    chat_id (int): The chat ID to be included in the callback data of each button.

    Returns:
    InlineKeyboardMarkup: The created InlineKeyboardMarkup instance.
    """
    keyboard = [
        [new_button(button["text"], chat_id, button["action"]) for button in row]
        for row in button_configs
    ]
    return InlineKeyboardMarkup(keyboard)


def authorize_user(bot: Bot, chat_id: int, user_id: int) -> bool:
    """
    Check if a user is an administrator or the creator of a chat.

    Args:
    bot (Bot): The Telegram Bot instance.
    chat_id (int): The ID of the chat.
    user_id (int): The ID of the user.

    Returns:
    bool: True if the user is an administrator or creator of the chat, False otherwise.
    """
    try:
        status = bot.get_chat_member(chat_id, user_id).status
        return status in ["creator", "administrator"]
    except Exception as e:
        return False


def get_chats_list(user_id: int, context: CallbackContext) -> Iterator[Dict[str, int]]:
    """
    Retrieve a list of chats where the user is an administrator or creator.

    Args:
    user_id (int): The ID of the user.
    context (CallbackContext): The callback context as provided by the Telegram API.

    Returns:
    Iterator[Dict[str, int]]: An iterator over dictionaries containing chat information.
    """
    with session_scope() as sess:
        users = sess.query(User).filter(User.user_id == user_id).all()
        # need that to terminate the session before running the expensive _get_chats_helper
        # AND be able to use the `users` list
        for user in users:
            sess.expunge(user)
    return _get_chats_helper(users, user_id, context.bot)


def _get_chats_helper(
    users: Iterator[User], user_id: int, bot: Bot
) -> Iterator[Dict[str, int]]:
    """
    Helper function to get chat information for each user.

    Args:
    users (Iterator[User]): An iterator over User instances.
    user_id (int): The ID of the user.
    bot (Bot): The Telegram Bot instance.

    Returns:
    Iterator[Dict[str, int]]: An iterator over dictionaries containing chat information.
    """
    for x in users:
        try:
            if authorize_user(bot, x.chat_id, user_id):
                yield {
                    "title": get_chat_name(bot, x.chat_id),
                    "id": x.chat_id,
                }
        except Exception as e:
            tg_logger.exception(e)


def create_chats_list_keyboard(
    user_chats: Iterator[Dict[str, int]], context: CallbackContext, user_id: int
) -> List[List[InlineKeyboardButton]]:
    """
    Create a keyboard layout for the list of chats where the user is an administrator or creator.

    Args:
    user_chats (Iterator[Dict[str, int]]): An iterator over dictionaries containing chat information.
    context (CallbackContext): The callback context as provided by the Telegram API.
    user_id (int): The ID of the user.

    Returns:
    List[List[InlineKeyboardButton]]: The created keyboard layout.
    """
    return [
        [new_button(chat["title"], chat["id"], constants.Actions.select_chat)]
        for chat in user_chats
        if authorize_user(context.bot, chat["id"], user_id)
    ]


def get_chat_name(bot: Bot, chat_id: int):
    return bot.get_chat(chat_id).title or str(chat_id)
