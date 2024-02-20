from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, Text, Boolean, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm.session import sessionmaker
from contextlib import asynccontextmanager

from src import constants
from src.texts import _

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
    
    @classmethod
    def get_new_chat(cls, chat_id: int):
        chat = cls(id=chat_id)
        # write default values from texts
        chat.on_new_chat_member_message = _("msg__new_chat_member")
        chat.on_known_new_chat_member_message = _("msg__known_new_chat_member")
        chat.on_introduce_message = _("msg__introduce")
        chat.on_kick_message = _("msg__kick")
        chat.notify_message = _("msg__notify")
        chat.on_introduce_message_update = _("msg__introduce_update")

        chat.kick_timeout = constants.default_kick_timeout_m
        chat.notify_timeout = constants.default_notify_timeout_m
        chat.whois_length = constants.default_whois_length
        return chat


class User(Base):
    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True)
    chat_id = Column(BigInteger, primary_key=True)

    whois = Column(Text, nullable=False)


engine = create_async_engine(constants.get_uri(), echo=False)
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
