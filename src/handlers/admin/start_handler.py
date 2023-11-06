from telegram import InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


from src.handlers.utils import admin
from src.texts import _


from .utils import get_chats_list, create_chats_list_keyboard


@admin
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /start command in a Telegram chat.

    Args:
    update (Update): The update object that represents the incoming update.
    context (ContextTypes.DEFAULT_TYPE): The context object that contains information about the current state of the bot.

    Returns:
    None
    """
    # Get the ID of the user who sent the message
    user_id = update.message.chat_id

    # Retrieve the list of chats where the user has administrative privileges
    user_chats = await get_chats_list(user_id, context)

    # If the user does not have administrative privileges in any chat, inform them
    if len(user_chats) == 0:
        await update.message.reply_text(_("msg__no_chats_available"))
        return

    # Create an inline keyboard with the list of available chats
    reply_markup = InlineKeyboardMarkup(
        create_chats_list_keyboard(user_chats, context, user_id)
    )

    # Send a message to the user with the inline keyboard
    await update.message.reply_text(_("msg__start_command"), reply_markup=reply_markup)
