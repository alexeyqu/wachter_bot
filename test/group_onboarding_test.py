import pytest
import json
from unittest.mock import AsyncMock, call

from src.handlers.group.my_chat_member_handler import my_chat_member_handler
from src.texts import _
from src import constants

from telegram import ChatMember, InlineKeyboardButton, InlineKeyboardMarkup


@pytest.mark.asyncio
async def test_add_bot_to_chat(mock_context):
    mock_update = AsyncMock()
    mock_update.effective_chat.id = 1000
    mock_update.my_chat_member.difference = lambda: {
        "status": (ChatMember.LEFT, ChatMember.MEMBER)
    }
    await my_chat_member_handler(mock_update, mock_context)
    mock_context.bot.send_message.assert_awaited_once_with(
        1000, _("msg__add_bot_to_chat")
    )


@pytest.mark.asyncio
async def test_make_bot_admin(mock_context, async_session):
    mock_update = AsyncMock()
    mock_update.effective_chat.id = 1000
    mock_update.effective_chat.title = "title"
    mock_update.effective_user.id = 1001
    mock_update.my_chat_member.difference = lambda: {
        "status": (ChatMember.MEMBER, ChatMember.ADMINISTRATOR)
    }
    await my_chat_member_handler(mock_update, mock_context)
    mock_context.bot.send_message.assert_has_calls(
        [
            call(
                1001,
                _("msg__make_admin_direct").format(chat_name="title"),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "Приветствия",
                                callback_data=json.dumps(
                                    {
                                        "chat_id": 1000,
                                        "action": constants.Actions.set_intro_settings,
                                    }
                                ),
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "Удаление и блокировка",
                                callback_data=json.dumps(
                                    {
                                        "chat_id": 1000,
                                        "action": constants.Actions.set_kick_bans_settings,
                                    }
                                ),
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "Назад",
                                callback_data=json.dumps(
                                    {
                                        "chat_id": 1000,
                                        "action": constants.Actions.back_to_chats,
                                    }
                                ),
                            )
                        ],
                    ]
                ),
            ),
            call(1000, _("msg__make_admin")),
        ],
        any_order=True,
    )
