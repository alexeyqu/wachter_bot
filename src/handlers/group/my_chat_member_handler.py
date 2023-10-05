import logging
from telegram import ChatMember, Update
from telegram.ext import CallbackContext

from src import constants
from src.model import Chat, session_scope


logger = logging.getLogger(__name__)


def my_chat_member_handler(update: Update, context: CallbackContext):
    old_status, new_status = update.my_chat_member.difference().get("status")

    if old_status == ChatMember.LEFT and new_status == ChatMember.MEMBER:
        # which means the bot was added to the chat
        context.bot.send_message(update.effective_chat.id, constants.on_add_bot_to_chat_message)
        return

    if old_status != ChatMember.ADMINISTRATOR and new_status == ChatMember.ADMINISTRATOR:
        # TODO: add chat to DB so that it is visible via /start
        # with session_scope() as sess:
        #     chat = sess.query(Chat).filter(Chat.id == update.effective_chat.id).first()

        #     if chat is None:
        #         chat = Chat(id=update.effective_chat.id)
        #         sess.add(chat)
        #         sess.commit()

        context.bot.send_message(update.effective_chat.id, constants.on_make_admin_message)
        # context.bot.send_message(update.effective_user.id, constants.on_make_admin_direct_message.format(chat_name=update.effective_chat.title))
        return
