import json
import time
from typing import Iterator, Dict, List

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from sqlalchemy import select

from src.logging import tg_logger
from src.model import User, session_scope
from src import constants


async def get_chat_name(bot, chat_id):
    chat = await bot.get_chat(chat_id)
    return chat.title or str(chat_id)


def new_button(text: str, chat_id: int, action) -> InlineKeyboardButton:
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


async def authorize_user(bot: Bot, chat_id: int, user_id: int) -> bool:
    """
    Asynchronously check if a user is an administrator or the creator of a chat.

    Args:
    bot (Bot): The Telegram Bot instance.
    chat_id (int): The ID of the chat.
    user_id (int): The ID of the user.

    Returns:
    bool: True if the user is an administrator or creator of the chat, False otherwise.
    """
    try:
        chat_member = await bot.get_chat_member(chat_id, user_id)
        return chat_member.status in ["creator", "administrator"]
    except Exception as e:
        print(f"Failed to check if user {user_id} is admin in chat {chat_id}: {e}")
        return False


async def get_chats_list(
    user_id: int, context: CallbackContext
) -> List[Dict[str, int]]:
    """
    Retrieve a list of chats where the user is an administrator or creator.

    This function queries the database for User instances associated with the provided
    user_id. For each User instance found, it checks whether the provided user_id
    is an authorized user of the associated chat. If so, the function retrieves the
    chat's title and id, and adds them to a list which is returned after all
    authorized chats have been processed.

    Args:
        user_id (int): The ID of the user.
        context (CallbackContext): The callback context as provided by the Telegram Bot API.

    Returns:
        List[Dict[str, int]]: A list of dictionaries, each containing the 'title' and 'id'
        of a chat where the user has administrative or creator rights.
    """
    time_start = time.time()
    async with session_scope() as session:  # Ensure this yields an AsyncSession object.
        result = await session.execute(select(User).filter(User.user_id == user_id))
        users = result.scalars().all()
    chats_list = []
    for user in users:
        try:
            if await authorize_user(context.bot, user.chat_id, user_id):
                chat_name = await get_chat_name(context.bot, user.chat_id)
                chats_list.append({"title": chat_name, "id": user.chat_id})
        except Exception as e:
            context.bot.logger.exception(
                e
            )  # Ensure your CallbackContext has a logger configured.
    tg_logger.info(f'get_chats_list time elapsed {time.time() - time_start}s')
    return chats_list


async def create_chats_list_keyboard(
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
        if await authorize_user(context.bot, chat["id"], user_id)
    ]
