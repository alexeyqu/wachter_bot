from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Text, Boolean, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import sessionmaker
from contextlib import contextmanager
import enum
import os

Base = declarative_base()

class Chat(Base):
    __tablename__ = 'chats'

    id = Column(BigInteger, primary_key=True)
    on_new_chat_member_message = Column(Text, nullable=False, default='Introduce yourself')
    on_introduce_message = Column(Text, nullable=False, default='Welcome')
    kick_timeout = Column(Integer, nullable=False, default=0)


    def __repr__(self):
        return f"<Chat(id={self.id})>"
        
engine = create_engine('postgresql://localhost:5432/wi_bot', echo=False)
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