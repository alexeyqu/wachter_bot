from telegram import Update
from telegram.ext import CallbackContext

from src.utils.actions_map import Button, actions_map


def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    action = query.data.get("action")
    handler = actions_map.get(Button(action))
    if handler is not None:
        return handler(update, context)
    else:
        # Handle the case where the action is not recognized
        query.answer("Unrecognized action")


def message_callback(update: Update, context: CallbackContext):
    if not update.message:
        update.message = update.edited_message

    chat_id = update.message.chat_id
    handler = actions_map.get("action")

    if handler is not None:
        return handler(update, context, chat_id)
    else:
        # Handle the case where the action is not recognized
        update.message.reply_text("Unrecognized action")
