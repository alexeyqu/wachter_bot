from telegram import ChatMember, Update
from telegram.ext import ContextTypes

from sqlalchemy import select

from src import constants
from src.model import Chat, User, session_scope
from src.handlers.admin.utils import new_keyboard_layout
from src.texts import _


async def my_chat_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    old_status, new_status = update.my_chat_member.difference().get("status")

    if old_status == ChatMember.LEFT and new_status == ChatMember.MEMBER:
        # which means the bot was added to the chat
        await context.bot.send_message(
            update.effective_chat.id, _("msg__add_bot_to_chat")
        )
        return

    if (
        old_status != ChatMember.ADMINISTRATOR
        and new_status == ChatMember.ADMINISTRATOR
    ):
        # which means the bot is now admin and can be used
        async with session_scope() as sess:
            result = await sess.execute(
                select(Chat).filter_by(id=update.effective_chat.id)
            )
            chat = result.scalars().first()

            if chat is None:
                chat = Chat.get_new_chat(update.effective_chat.id)
                sess.add(chat)
                # hack with adding an empty #whois to prevent slow /start cmd
                # TODO after v1.0: rework the DB schema
                user = User(
                    chat_id=update.effective_chat.id,
                    user_id=update.effective_user.id,
                    whois="",
                )
                await sess.merge(user)
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
                await context.bot.send_message(
                    update.effective_user.id,
                    _("msg__make_admin_direct").format(
                        chat_name=update.effective_chat.title
                    ),
                    reply_markup=reply_markup,
                )

        await context.bot.send_message(update.effective_chat.id, _("msg__make_admin"))
        return
