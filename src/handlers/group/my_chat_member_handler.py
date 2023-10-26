from telegram import ChatMember, Update
from telegram.ext import CallbackContext

from src import constants
from src.model import Chat, User, session_scope


def my_chat_member_handler(update: Update, context: CallbackContext):
    old_status, new_status = update.my_chat_member.difference().get("status")

    if old_status == ChatMember.LEFT and new_status == ChatMember.MEMBER:
        # which means the bot was added to the chat
        context.bot.send_message(
            update.effective_chat.id, constants.on_add_bot_to_chat_message
        )
        return

    if (
        old_status != ChatMember.ADMINISTRATOR
        and new_status == ChatMember.ADMINISTRATOR
    ):
        # which means the bot is not admin and can be used
        with session_scope() as sess:
            chat = sess.query(Chat).filter(Chat.id == update.effective_chat.id).first()

            if chat is None:
                chat = Chat(id=update.effective_chat.id)
                # write default
                chat.on_new_chat_member_message = constants.on_new_chat_member_message
                chat.on_known_new_chat_member_message = (
                    constants.on_known_new_chat_member_message
                )
                chat.on_introduce_message = constants.on_introduce_message
                chat.on_kick_message = constants.on_kick_message
                chat.notify_message = constants.notify_message
                chat.on_introduce_message_update = constants.on_introduce_message_update

                sess.add(chat)
                # hack with adding an empty #whois to prevent slow /start cmd
                # TODO after v1.0: rework the DB schema
                user = User(
                    chat_id=update.effective_chat.id,
                    user_id=update.effective_user.id,
                    whois="",
                )
                sess.merge(user)
                # notify the admin about a new chat
                context.bot.send_message(
                    update.effective_user.id,
                    constants.on_make_admin_direct_message.format(
                        chat_name=update.effective_chat.title
                    ),
                )

        context.bot.send_message(
            update.effective_chat.id, constants.on_make_admin_message
        )
        return
