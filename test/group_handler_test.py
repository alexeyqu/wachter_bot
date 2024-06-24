import pytest
from sqlalchemy import select
from unittest.mock import patch
import os

with patch.dict(
    "os.environ",
    {
        "TELEGRAM_TOKEN": "dummy_token",
        "TELEGRAM_ERROR_CHAT_ID": "dummy_chat_id",
        "UPTRACE_DSN": "dummy_dsn",
        "DEPLOYMENT_ENVIRONMENT": "testing",
    },
):
    from src.handlers.group.group_handler import on_hashtag_message
    from src.model import User, Chat
from src.texts import _

from telegram.constants import ParseMode


async def mock_mention_markdown(bot, chat_id, user_id, message):
    # Replace %USER_MENTION% with a default string
    return message.replace("%USER_MENTION%", "@example_user")


@pytest.mark.asyncio
async def test_on_hashtag_message_new_user(
    mock_update, mock_context, async_session, populate_db, mocker
):
    # Simulate the Incoming Message
    chat_id = -3  # Example group chat ID (negative for groups)
    user_id = 3  # Example new user ID
    mock_update.effective_message.chat_id = chat_id
    mock_update.effective_message.from_user.id = user_id
    mock_update.effective_message.text = "#whois I am new here dkgjldskfjglkdfjglkdfsj lgkjdsflökgjldösfjglsdfjgölkdsfjglöksdjfglöksdfjglöksdfjg"

    mocker.patch("src.handlers.group.group_handler.is_whois", return_value=True)
    mocker.patch(
        "src.handlers.group.group_handler._mention_markdown",
        return_value="@example_user",
    )
    mocker.patch(
        "src.handlers.group.group_handler.remove_user_jobs_from_queue",
        return_value=True,
    )
    mocker.patch(
        "src.handlers.group.group_handler.whois_counter.add",
        return_value=True,
    )

    await on_hashtag_message(mock_update, mock_context)

    # Check if the reply message was sent
    assert mock_update.effective_message.reply_text.await_count == 1

    # Verify that the new user is added to the database
    async with async_session as session:
        result = await session.execute(
            select(User).where(User.chat_id == chat_id, User.user_id == user_id)
        )
        user = result.scalars().first()
        assert user is not None
        assert (
            user.whois
            == "#whois I am new here dkgjldskfjglkdfjglkdfsj lgkjdsflökgjldösfjglsdfjgölkdsfjglöksdjfglöksdfjglöksdfjg"
        )


@pytest.mark.asyncio
async def test_on_hashtag_message_short_whois(
    mock_update, mock_context, async_session, populate_db, mocker
):
    # Simulate the Incoming Message
    chat_id = -3  # Example group chat ID (negative for groups)
    user_id = 3  # Example new user ID
    mock_update.effective_message.chat_id = chat_id
    mock_update.effective_message.from_user.id = user_id
    mock_update.effective_message.text = "#whois I am new here"

    mocker.patch("src.handlers.group.group_handler.is_whois", return_value=True)
    mocker.patch(
        "src.handlers.group.group_handler._mention_markdown",
        side_effect=mock_mention_markdown,
    )

    await on_hashtag_message(mock_update, mock_context)

    async with async_session as session:
        try:
            result = await session.execute(
                select(Chat.whois_length).where(Chat.id == chat_id)
            )
            whois_length = result.scalar_one()
            print(whois_length)
        except Exception as e:
            print(f"Error during query execution: {e}")
            raise
            print()
    expected_reply = _("msg__short_whois").format(whois_length=whois_length)
    # Fetch the actual reply text
    actual_reply_call = mock_update.effective_message.reply_text.call_args
    actual_reply = actual_reply_call[1]["text"] if actual_reply_call else None

    # Improved assertion with detailed error message
    assert (
        actual_reply == expected_reply
    ), f"Assertion failed: Expected reply text '{expected_reply}' but got '{actual_reply}'."
