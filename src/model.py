from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, Text, Boolean, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm.session import sessionmaker
from contextlib import asynccontextmanager
import os

Base = declarative_base()


class Chat(Base):
    __tablename__ = "chats"

    id = Column(BigInteger, primary_key=True)

    on_new_chat_member_message = Column(
        Text,
        nullable=False,
    )
    on_known_new_chat_member_message = Column(
        Text,
        nullable=False,
    )
    on_introduce_message = Column(
        Text,
        nullable=False,
    )
    on_kick_message = Column(
        Text,
        nullable=False,
    )
    notify_message = Column(
        Text,
        nullable=False,
    )
    regex_filter = Column(Text, nullable=True)  # keeping that in db for now, unused
    filter_only_new_users = Column(
        Boolean, nullable=False, default=False
    )  # keeping that in db for now, unused
    kick_timeout = Column(
        Integer,
        nullable=False,
    )
    notify_timeout = Column(
        Integer,
        nullable=False,
    )
    whois_length = Column(
        Integer,
        nullable=False,
    )
    on_introduce_message_update = Column(
        Text,
        nullable=False,
    )

    def __repr__(self):
        return f"<Chat(id={self.id})>"


class User(Base):
    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True)
    chat_id = Column(BigInteger, primary_key=True)

    whois = Column(Text, nullable=False)


def get_uri():
    if os.environ.get("TESTING") == "true":
        return os.environ.get(
            "DATABASE_URL", "sqlite+aiosqlite:///:memory:?cache=shared"
        )
    return os.environ.get(
        "DATABASE_URL", "postgresql+asyncpg://user:password@wachter-db/db"
    )


engine = create_async_engine(get_uri(), echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def session_scope():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise
        finally:
            await session.close()


def orm_to_dict(obj):
    return obj._asdict()
