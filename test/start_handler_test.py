import pytest
import json
from unittest.mock import patch

from src.handlers.admin.start_handler import start_handler
from src import constants
from src.texts import _

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


@pytest.mark.asyncio
async def test_start_handler_no_chats(mock_update, mock_context, populate_db):
    mock_update.message.chat_id = 3
    await start_handler(mock_update, mock_context)
    mock_update.message.reply_text.assert_awaited_once_with(
        _("msg__no_chats_available")
    )


@pytest.mark.asyncio
async def test_start_handler_basic(mock_update, mock_context, mocker):
    mock_update.message.chat_id = 1
    mocker.patch("src.handlers.admin.utils.authorize_user", return_value=True)
    mocker.patch("src.handlers.admin.utils.get_chat_name", return_value="Chat")
    await start_handler(mock_update, mock_context)
    mock_update.message.reply_text.assert_awaited_once_with(
        _("msg__start_command"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=(
                (
                    InlineKeyboardButton(
                        callback_data='{"chat_id": 1, "action": 2}', text="Chat"
                    ),
                ),
                (
                    InlineKeyboardButton(
                        callback_data='{"chat_id": 2, "action": 2}', text="Chat"
                    ),
                ),
            )
        ),
    )
