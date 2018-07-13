from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Text, Boolean, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import sessionmaker
from contextlib import contextmanager
import enum
import os
from sqlalchemy import inspect

Base = declarative_base()


class Chat(Base):
    __tablename__ = 'chats'

    id = Column(BigInteger, primary_key=True)

    on_new_chat_member_message = Column(Text, nullable=False, default='Представьтесь, пожалуйста')
    on_known_new_chat_member_message = Column(Text, nullable=False, default='Добро пожаловать')
    on_introduce_message = Column(Text, nullable=False, default='Добро пожаловать')
    notify_message = Column(Text, nullable=False, default='Представьтесь, пожалуйста')
    kick_timeout = Column(Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<Chat(id={self.id})>"


class User(Base):
    __tablename__ = 'users'

    user_id = Column(BigInteger, primary_key=True)
    chat_id = Column(BigInteger, primary_key=True)

    whois = Column(Text, nullable=False)


def get_uri():
    return os.environ.get('DATABASE_URL', 'postgresql://localhost:5432/wachter')


engine = create_engine(get_uri(), echo=False)
Session = sessionmaker(autoflush=True, bind=engine)


@contextmanager
def session_scope():
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

def orm_to_dict(obj):
    return obj._asdict()
