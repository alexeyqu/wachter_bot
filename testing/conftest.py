import sys
import os
import pytest, pytest_asyncio, asyncio, json
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from src import constants
from src.model import engine, User, Chat

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))


@pytest.fixture
def mock_update():
    callback_query = AsyncMock()
    callback_query.data = json.dumps({"action": constants.Actions.start_select_chat})

    message_mock = MagicMock()
    message_mock.chat_id = 12345
    message_mock.message_id = 67890
    message_mock.reply_text = AsyncMock()

    update = AsyncMock()
    update.callback_query = callback_query
    update.message = message_mock
    return update


@pytest.fixture
def mock_context():
    context = AsyncMock()
    bot_mock = AsyncMock()
    bot_mock.edit_message_text = AsyncMock()
    context.job_queue.run_once = MagicMock()
    context.bot = bot_mock
    return context


@pytest.fixture(scope="function", autouse=True)
def mock_get_uri():
    with patch("src.model.get_uri") as mock_get_uri:
        mock_get_uri.return_value = "sqlite+aiosqlite:///:memory:?cache=shared"
        yield


# Fixture to set up an in-memory SQLite database
@pytest_asyncio.fixture(scope="function")
async def async_engine():
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS users;"))
        await conn.execute(text("DROP TABLE IF EXISTS chats;"))
        await conn.execute(
            text(
                """
            CREATE TABLE chats (
                id INTEGER PRIMARY KEY,
                on_new_chat_member_message TEXT NOT NULL,
                on_known_new_chat_member_message TEXT NOT NULL,
                on_introduce_message TEXT NOT NULL,
                on_kick_message TEXT NOT NULL,
                notify_message TEXT NOT NULL,
                regex_filter TEXT,
                filter_only_new_users BOOLEAN NOT NULL DEFAULT FALSE,
                kick_timeout INTEGER NOT NULL,
                notify_timeout INTEGER NOT NULL,
                whois_length INTEGER NOT NULL,
                on_introduce_message_update TEXT NOT NULL
            );
        """
            )
        )
        await conn.execute(
            text(
                """
            CREATE TABLE users (
                user_id INTEGER,
                chat_id INTEGER,
                whois TEXT NOT NULL,
                PRIMARY KEY (user_id, chat_id)
            );
        """
            )
        )
    return engine


# Fixture for creating a new session for each test
@pytest_asyncio.fixture(scope="function")
async def async_session(async_engine):
    async_session_local = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_local() as session:
        yield session


@pytest_asyncio.fixture
async def populate_db(async_session):
    # Define user data
    user_data = [
        (1, 1, "User 1 in Chat 1"),
        (1, 2, "User 1 in Chat 2"),
        (2, 2, "User 2 in Chat 2"),
        (2, 3, "User 2 in Chat 3"),
        (3, None, "User 3, no Chats"),
    ]

    # Define chat data
    chat_data = [
        (
            1,
            "Welcome to Chat 1",
            "Message for known members in Chat 1",
            "Introduce in Chat 1",
            "Kick message in Chat 1",
            "Notify message in Chat 1",
            None,
            False,
            30,
            60,
            100,
            "Update Introduce in Chat 1",
        ),
        (
            2,
            "Welcome to Chat 2",
            "Message for known members in Chat 2",
            "Introduce in Chat 2",
            "Kick message in Chat 2",
            "Notify message in Chat 2",
            None,
            False,
            30,
            60,
            100,
            "Update Introduce in Chat 2",
        ),
        (
            -3,
            "Welcome to Chat 2",
            "Message for known members in Chat 2",
            "Introduce in Chat 2",
            "Kick message in Chat 2",
            "Notify message in Chat 2",
            None,
            False,
            30,
            60,
            100,
            "Update Introduce in Chat 2",
        ),
    ]

    # Create objects using list comprehension
    users = [
        User(user_id=uid, chat_id=cid, whois=whois) for uid, cid, whois in user_data
    ]

    chats = [
        Chat(
            id=cid,
            on_new_chat_member_message=welcome,
            on_known_new_chat_member_message=known,
            on_introduce_message=introduce,
            on_kick_message=kick,
            notify_message=notify,
            regex_filter=regex,
            filter_only_new_users=filter_new,
            kick_timeout=kick_timeout,
            notify_timeout=notify_timeout,
            whois_length=whois_length,
            on_introduce_message_update=introduce_update,
        )
        for cid, welcome, known, introduce, kick, notify, regex, filter_new, kick_timeout, notify_timeout, whois_length, introduce_update in chat_data
    ]

    async_session.add_all(users + chats)

    await async_session.commit()
