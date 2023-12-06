import json
import pytest, pytest_asyncio, asyncio

# from conftest import function_scoped_event_loop, session_scoped_event_loop

from src.handlers.admin.menu_handler import button_handler
from src.texts import _
from src import constants


from unittest.mock import patch

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from telegram.constants import ParseMode


@pytest.mark.asyncio
async def test_button_handler_no_chats(mock_update, mock_context, populate_db):
    mock_update.callback_query.from_user.id = 3
    await button_handler(mock_update, mock_context)
    # Assert that the expected message was sent
    mock_update.message.reply_text.assert_awaited_once_with(
        _("msg__no_chats_available")
    )


@pytest.mark.asyncio
async def test_button_handler_basic_start(mock_update, mock_context, mocker):
    mock_update.callback_query.from_user.id = 1
    mocker.patch("src.handlers.admin.utils.authorize_user", return_value=True)
    mocker.patch("src.handlers.admin.utils.get_chat_name", return_value="Chat")
    await button_handler(mock_update, mock_context)
    mock_context.bot.edit_message_text.assert_awaited_once_with(
        _("msg__start_command"),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Chat",
                        callback_data=json.dumps(
                            {"chat_id": 1, "action": constants.Actions.select_chat}
                        ),
                    )
                ],
                [
                    InlineKeyboardButton(
                        "Chat",
                        callback_data=json.dumps(
                            {"chat_id": 2, "action": constants.Actions.select_chat}
                        ),
                    )
                ],
            ]
        ),
        chat_id=mock_update.callback_query.message.chat_id,
        message_id=mock_update.callback_query.message.message_id,
    )


@pytest.mark.asyncio
async def test_select_chat_action(mock_update, mock_context, mocker):
    # Set the data for the select_chat action
    action = constants.Actions.select_chat
    selected_chat_id = 1
    chat_name = "Chat"

    # Mock the data being received from the callback_query
    mock_update.callback_query.data = json.dumps(
        {"action": action, "chat_id": selected_chat_id}
    )
    mocker.patch("src.handlers.admin.utils.get_chat_name", return_value="Chat")

    expected_keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=_("btn__intro"),
                    callback_data=json.dumps(
                        {
                            "chat_id": selected_chat_id,
                            "action": constants.Actions.set_intro_settings,
                        }
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("btn__kicks"),
                    callback_data=json.dumps(
                        {
                            "chat_id": selected_chat_id,
                            "action": constants.Actions.set_kick_bans_settings,
                        }
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("btn__back_to_chats"),
                    callback_data=json.dumps(
                        {
                            "chat_id": selected_chat_id,
                            "action": constants.Actions.back_to_chats,
                        }
                    ),
                )
            ],
        ]
    )

    await button_handler(mock_update, mock_context)
    actual_call = mock_context.bot.edit_message_text.call_args[
        1
    ]  # This gets the kwargs of the last call
    assert actual_call["reply_markup"] == expected_keyboard


@pytest.mark.asyncio
async def test_set_kick_bans_settings(mock_update, mock_context, mocker):
    action = constants.Actions.set_kick_bans_settings
    selected_chat_id = 1
    mock_update.callback_query.data = json.dumps(
        {"action": action, "chat_id": selected_chat_id}
    )
    await button_handler(mock_update, mock_context)

    expected_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("btn__current_settings"),
                    callback_data=json.dumps(
                        {
                            "chat_id": selected_chat_id,
                            "action": constants.Actions.get_current_kick_settings,
                        }
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("btn__change_kick_timeout"),
                    callback_data=json.dumps(
                        {
                            "chat_id": selected_chat_id,
                            "action": constants.Actions.set_kick_timeout,
                        }
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("btn__change_kick_message"),
                    callback_data=json.dumps(
                        {
                            "chat_id": selected_chat_id,
                            "action": constants.Actions.set_on_kick_message,
                        }
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("btn__back"),
                    callback_data=json.dumps(
                        {
                            "chat_id": selected_chat_id,
                            "action": constants.Actions.select_chat,
                        }
                    ),
                )
            ],
        ]
    )

    mock_context.bot.edit_message_reply_markup.assert_awaited_once_with(
        reply_markup=expected_keyboard,
        chat_id=mock_update.callback_query.message.chat_id,
        message_id=mock_update.callback_query.message.message_id,
    )


@pytest.mark.asyncio
async def test_back_to_chats(mock_update, mock_context, mocker):
    mock_update.callback_query.from_user.id = 1
    mocker.patch("src.handlers.admin.utils.authorize_user", return_value=True)
    mocker.patch("src.handlers.admin.utils.get_chat_name", return_value="Chat")
    await button_handler(mock_update, mock_context)
    mock_context.bot.edit_message_text.assert_awaited_once_with(
        _("msg__start_command"),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Chat",
                        callback_data=json.dumps(
                            {"chat_id": 1, "action": constants.Actions.select_chat}
                        ),
                    )
                ],
                [
                    InlineKeyboardButton(
                        "Chat",
                        callback_data=json.dumps(
                            {"chat_id": 2, "action": constants.Actions.select_chat}
                        ),
                    )
                ],
            ]
        ),
        chat_id=mock_update.callback_query.message.chat_id,
        message_id=mock_update.callback_query.message.message_id,
    )


@pytest.mark.asyncio
async def test_set_on_new_chat_member_message_response(
    mock_update, mock_context, mocker
):
    action = constants.Actions.set_on_new_chat_member_message_response
    selected_chat_id = 1
    mock_update.callback_query.data = json.dumps(
        {"action": action, "chat_id": selected_chat_id}
    )

    await button_handler(mock_update, mock_context)

    mock_context.bot.edit_message_text.assert_awaited_once_with(
        text=_("msg__set_new_welcome_message"),
        chat_id=mock_update.callback_query.message.chat_id,
        message_id=mock_update.callback_query.message.message_id,
        parse_mode=ParseMode.MARKDOWN,
    )


@pytest.mark.asyncio
async def test_set_kick_timeout(mock_update, mock_context, mocker):
    action = constants.Actions.set_kick_timeout
    selected_chat_id = 1
    mock_update.callback_query.data = json.dumps(
        {"action": action, "chat_id": selected_chat_id}
    )

    await button_handler(mock_update, mock_context)

    mock_context.bot.edit_message_text.assert_awaited_once_with(
        text=_("msg__set_new_kick_timout"),
        chat_id=mock_update.callback_query.message.chat_id,
        message_id=mock_update.callback_query.message.message_id,
    )


@pytest.mark.asyncio
async def test_set_on_known_new_chat_member_message_response(mock_update, mock_context):
    action = constants.Actions.set_on_known_new_chat_member_message_response
    selected_chat_id = 1
    mock_update.callback_query.data = json.dumps(
        {"action": action, "chat_id": selected_chat_id}
    )

    await button_handler(mock_update, mock_context)

    mock_context.bot.edit_message_text.assert_awaited_once_with(
        text=_("msg__set_new_rewelcome_message"),
        chat_id=mock_update.callback_query.message.chat_id,
        message_id=mock_update.callback_query.message.message_id,
        parse_mode=ParseMode.MARKDOWN,
    )


@pytest.mark.asyncio
async def test_set_new_notify_message(mock_update, mock_context, mocker):
    action = constants.Actions.set_notify_message
    selected_chat_id = 1
    mock_update.callback_query.data = json.dumps(
        {"action": action, "chat_id": selected_chat_id}
    )

    await button_handler(mock_update, mock_context)

    mock_context.bot.edit_message_text.assert_awaited_once_with(
        text=_("msg__set_new_notify_message"),
        chat_id=mock_update.callback_query.message.chat_id,
        message_id=mock_update.callback_query.message.message_id,
        parse_mode=ParseMode.MARKDOWN,
    )


@pytest.mark.asyncio
async def test_set_on_new_chat_member_message_response(
    mock_update, mock_context, mocker
):
    action = constants.Actions.set_on_new_chat_member_message_response
    selected_chat_id = 1
    mock_update.callback_query.data = json.dumps(
        {"action": action, "chat_id": selected_chat_id}
    )

    await button_handler(mock_update, mock_context)

    mock_context.bot.edit_message_text.assert_awaited_once_with(
        text=_("msg__set_new_welcome_message"),
        chat_id=mock_update.callback_query.message.chat_id,
        message_id=mock_update.callback_query.message.message_id,
        parse_mode=ParseMode.MARKDOWN,
    )


@pytest.mark.asyncio
async def test_set_on_successful_introducion_response(
    mock_update, mock_context, mocker
):
    action = constants.Actions.set_on_successful_introducion_response
    selected_chat_id = 1
    mock_update.callback_query.data = json.dumps(
        {"action": action, "chat_id": selected_chat_id}
    )

    await button_handler(mock_update, mock_context)

    mock_context.bot.edit_message_text.assert_awaited_once_with(
        text=_("msg__set_new_sucess_message"),
        chat_id=mock_update.callback_query.message.chat_id,
        message_id=mock_update.callback_query.message.message_id,
        parse_mode=ParseMode.MARKDOWN,
    )


@pytest.mark.asyncio
async def test_set_whois_length(mock_update, mock_context, mocker):
    action = constants.Actions.set_whois_length
    selected_chat_id = 1
    mock_update.callback_query.data = json.dumps(
        {"action": action, "chat_id": selected_chat_id}
    )

    await button_handler(mock_update, mock_context)

    mock_context.bot.edit_message_text.assert_awaited_once_with(
        text=_("msg__set_new_whois_length"),
        chat_id=mock_update.callback_query.message.chat_id,
        message_id=mock_update.callback_query.message.message_id,
    )


@pytest.mark.asyncio
async def test_set_on_kick_message(mock_update, mock_context, mocker):
    action = constants.Actions.set_on_kick_message
    selected_chat_id = 1
    mock_update.callback_query.data = json.dumps(
        {"action": action, "chat_id": selected_chat_id}
    )

    await button_handler(mock_update, mock_context)

    mock_context.bot.edit_message_text.assert_awaited_once_with(
        text=_("msg__set_new_kick_message"),
        chat_id=mock_update.callback_query.message.chat_id,
        message_id=mock_update.callback_query.message.message_id,
        parse_mode=ParseMode.MARKDOWN,
    )


@pytest.mark.asyncio
async def test_set_notify_timeout(mock_update, mock_context, mocker):
    action = constants.Actions.set_notify_timeout
    selected_chat_id = 1
    mock_update.callback_query.data = json.dumps(
        {"action": action, "chat_id": selected_chat_id}
    )

    await button_handler(mock_update, mock_context)

    mock_context.bot.edit_message_text.assert_awaited_once_with(
        text=_("msg__set_new_notify_timeout"),
        chat_id=mock_update.callback_query.message.chat_id,
        message_id=mock_update.callback_query.message.message_id,
    )


@pytest.mark.asyncio
async def test_set_on_introduce_message_update(mock_update, mock_context, mocker):
    action = constants.Actions.set_on_introduce_message_update
    selected_chat_id = 1
    mock_update.callback_query.data = json.dumps(
        {"action": action, "chat_id": selected_chat_id}
    )

    await button_handler(mock_update, mock_context)

    mock_context.bot.edit_message_text.assert_awaited_once_with(
        text=_("msg__set_new_whois_message"),
        chat_id=mock_update.callback_query.message.chat_id,
        message_id=mock_update.callback_query.message.message_id,
        parse_mode=ParseMode.MARKDOWN,
    )
