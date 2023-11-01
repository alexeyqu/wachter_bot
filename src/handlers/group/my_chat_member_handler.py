from telegram import ChatMember, Update
from telegram.ext import CallbackContext

from src import constants
from src.model import Chat, User, session_scope
from src.handlers.admin.utils import new_keyboard_layout
from src.texts import _


def my_chat_member_handler(update: Update, context: CallbackContext):
    old_status, new_status = update.my_chat_member.difference().get("status")

    if old_status == ChatMember.LEFT and new_status == ChatMember.MEMBER:
        # which means the bot was added to the chat
        context.bot.send_message(update.effective_chat.id, _("msg__add_bot_to_chat"))
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
                # write default values from texts
                chat.on_new_chat_member_message = _("msg__new_chat_member")
                chat.on_known_new_chat_member_message = _("msg__known_new_chat_member")
                chat.on_introduce_message = _("msg__introduce")
                chat.on_kick_message = _("msg__kick")
                chat.notify_message = _("msg__notify")
                chat.on_introduce_message_update = _("msg__introduce_update")

                chat.kick_timeout = constants.default_kick_timeout
                chat.notify_timeout = constants.default_notify_timeout
                chat.whois_length = constants.default_whois_length

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
                button_configs = [
                    [
                        {
                            "text": "Приветствия",
                            "action": constants.Actions.set_intro_settings,
                        }
                    ],
                    [
                        {
                            "text": "Удаление и блокировка",
                            "action": constants.Actions.set_kick_bans_settings,
                        }
                    ],
                    [{"text": "Назад", "action": constants.Actions.back_to_chats}],
                ]
                reply_markup = new_keyboard_layout(
                    button_configs, update.effective_chat.id
                )
                context.bot.send_message(
                    update.effective_user.id,
                    _("msg__make_admin_direct").format(
                        chat_name=update.effective_chat.title
                    ),
                    reply_markup=reply_markup,
                )

        context.bot.send_message(update.effective_chat.id, _("msg__make_admin"))
        return
