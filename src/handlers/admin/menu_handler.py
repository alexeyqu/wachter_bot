import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.ext import CallbackContext
from datetime import datetime, timedelta

from src import constants
from src.model import Chat, User, session_scope

from src.handlers.group.group_handler import on_kick_timeout, on_notify_timeout

from .utils import authorize_user


# todo rework into callback folder
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = json.loads(query.data)

    if data["action"] == constants.Actions.start_select_chat:
        with session_scope() as sess:
            user_id = query.from_user.id
            users = sess.query(User).filter(User.user_id == user_id)
            user_chats = [
                {
                    "title": context.bot.get_chat(x.chat_id).title or x.chat_id,
                    "id": x.chat_id,
                }
                for x in users
            ]

        if len(user_chats) == 0:
            update.message.reply_text("У вас нет доступных чатов.")
            return

        keyboard = [
            [
                InlineKeyboardButton(
                    chat["title"],
                    callback_data=json.dumps(
                        {"chat_id": chat["id"], "action": constants.Actions.select_chat}
                    ),
                )
            ]
            for chat in user_chats
            if authorize_user(context.bot, chat["id"], user_id)
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.edit_message_reply_markup(
            reply_markup=reply_markup,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )

    if data["action"] == constants.Actions.select_chat:
        selected_chat_id = data["chat_id"]
        keyboard = [
            [
                InlineKeyboardButton(
                    "Изменить таймаут кика",
                    callback_data=json.dumps(
                        {
                            "chat_id": selected_chat_id,
                            "action": constants.Actions.set_kick_timeout,
                        }
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "Изменить сообщение при входе в чат",
                    callback_data=json.dumps(
                        {
                            "chat_id": selected_chat_id,
                            "action": constants.Actions.set_on_new_chat_member_message_response,
                        }
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "Изменить сообщение при перезаходе в чат",
                    callback_data=json.dumps(
                        {
                            "chat_id": selected_chat_id,
                            "action": constants.Actions.set_on_known_new_chat_member_message_response,
                        }
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "Изменить сообщение после успешного представления",
                    callback_data=json.dumps(
                        {
                            "chat_id": selected_chat_id,
                            "action": constants.Actions.set_on_successful_introducion_response,
                        }
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "Изменить сообщение напоминания",
                    callback_data=json.dumps(
                        {
                            "chat_id": selected_chat_id,
                            "action": constants.Actions.set_notify_message,
                        }
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "Изменить сообщение после кика",
                    callback_data=json.dumps(
                        {
                            "chat_id": selected_chat_id,
                            "action": constants.Actions.set_on_kick_message,
                        }
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "Получить текущие настройки",
                    callback_data=json.dumps(
                        {
                            "chat_id": selected_chat_id,
                            "action": constants.Actions.get_current_settings,
                        }
                    ),
                )
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.edit_message_reply_markup(
            reply_markup=reply_markup,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )

    elif data["action"] in [
        constants.Actions.set_on_new_chat_member_message_response,
        constants.Actions.set_kick_timeout,
        constants.Actions.set_notify_message,
        constants.Actions.set_on_known_new_chat_member_message_response,
        constants.Actions.set_on_successful_introducion_response,
        constants.Actions.set_on_kick_message,
    ]:
        context.bot.edit_message_text(
            text="Отправьте новое значение",
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )
        context.user_data["chat_id"] = data["chat_id"]
        context.user_data["action"] = data["action"]

    elif data["action"] == constants.Actions.get_current_settings:
        keyboard = [
            [
                InlineKeyboardButton(
                    "К настройке чата",
                    callback_data=json.dumps(
                        {
                            "chat_id": data["chat_id"],
                            "action": constants.Actions.select_chat,
                        }
                    ),
                ),
                InlineKeyboardButton(
                    "К списку чатов",
                    callback_data=json.dumps(
                        {"action": constants.Actions.start_select_chat}
                    ),
                ),
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        with session_scope() as sess:
            chat = sess.query(Chat).filter(Chat.id == data["chat_id"]).first()
            context.bot.edit_message_text(
                text=constants.get_settings_message.format(**chat.__dict__),
                parse_mode=ParseMode.MARKDOWN,
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                reply_markup=reply_markup,
            )

        context.user_data["action"] = None


def message_handler(update: Update, context: CallbackContext):
    if not update.message:
        update.message = update.edited_message

    chat_id = update.message.chat_id

    if chat_id > 0:
        action = context.user_data.get("action")

        if action is None:
            return

        chat_id = context.user_data["chat_id"]

        if action == constants.Actions.set_kick_timeout:
            message = update.message.text
            try:
                timeout = int(message)
                assert timeout >= 0
            except:
                update.message.reply_text(constants.on_failed_set_kick_timeout_response)
                return
            with session_scope() as sess:
                chat = Chat(id=chat_id, kick_timeout=timeout)
                sess.merge(chat)
            context.user_data["action"] = None

            for job in context.job_queue.jobs():
                if job.name in [on_kick_timeout.__name__, on_notify_timeout.__name__]:
                    job_context = job.context
                    job_creation_time = datetime.fromtimestamp(
                        job_context.get("creation_time")
                    )
                    new_timeout = job_creation_time + timedelta(seconds=timeout * 60)
                    if job.name == on_kick_timeout.__name__:
                        if new_timeout < datetime.now():
                            new_timeout = 0
                        next_job_func = on_kick_timeout
                    else:
                        new_timeout = new_timeout - timedelta(
                            seconds=constants.notify_delta * 60
                        )
                        next_job_func = on_notify_timeout

                    job.schedule_removal()
                    job_context["timeout"] = new_timeout
                    job = context.job_queue.run_once(
                        next_job_func, new_timeout, context=job_context
                    )

            keyboard = [
                [
                    InlineKeyboardButton(
                        "К настройке чата",
                        callback_data=json.dumps(
                            {
                                "chat_id": chat_id,
                                "action": constants.Actions.select_chat,
                            }
                        ),
                    ),
                    InlineKeyboardButton(
                        "К списку чатов",
                        callback_data=json.dumps(
                            {"action": constants.Actions.start_select_chat}
                        ),
                    ),
                ],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(
                constants.on_success_set_kick_timeout_response,
                reply_markup=reply_markup,
            )

        elif action in [
            constants.Actions.set_on_new_chat_member_message_response,
            constants.Actions.set_notify_message,
            constants.Actions.set_on_known_new_chat_member_message_response,
            constants.Actions.set_on_successful_introducion_response,
            constants.Actions.set_on_kick_message,
        ]:
            message = update.message.text_markdown
            with session_scope() as sess:
                if action == constants.Actions.set_on_new_chat_member_message_response:
                    chat = Chat(id=chat_id, on_new_chat_member_message=message)
                if (
                    action
                    == constants.Actions.set_on_known_new_chat_member_message_response
                ):
                    chat = Chat(id=chat_id, on_known_new_chat_member_message=message)
                if action == constants.Actions.set_on_successful_introducion_response:
                    chat = Chat(id=chat_id, on_introduce_message=message)
                if action == constants.Actions.set_notify_message:
                    chat = Chat(id=chat_id, notify_message=message)
                if action == constants.Actions.set_on_kick_message:
                    chat = Chat(id=chat_id, on_kick_message=message)
                sess.merge(chat)

            context.user_data["action"] = None

            keyboard = [
                [
                    InlineKeyboardButton(
                        "К настройке чата",
                        callback_data=json.dumps(
                            {
                                "chat_id": chat_id,
                                "action": constants.Actions.select_chat,
                            }
                        ),
                    ),
                    InlineKeyboardButton(
                        "К списку чатов",
                        callback_data=json.dumps(
                            {"action": constants.Actions.start_select_chat}
                        ),
                    ),
                ],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(
                constants.on_set_new_message, reply_markup=reply_markup
            )
