import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.ext import CallbackContext
from datetime import datetime, timedelta

from src import constants
from src.model import Chat, session_scope

from src.handlers.group.group_handler import on_kick_timeout, on_notify_timeout

from .utils import get_chats_list, create_chats_list_keyboard


def _job_rescheduling_helper(job_func, timeout, context, chat_id):
    for job in context.job_queue.jobs():
        if job.name == job_func.__name__:
            job_context = job.context
            job_creation_time = datetime.fromtimestamp(job_context.get("creation_time"))
            new_timeout = job_creation_time + timedelta(seconds=timeout * 60)
            if job.name == job_func.__name__:
                if new_timeout < datetime.now():
                    new_timeout = 0
            job.schedule_removal()
            if job_func == on_notify_timeout:
                with session_scope() as sess:
                    chat = sess.query(Chat).filter(Chat.id == chat_id).first()
                    kick_timeout = chat.kick_timeout
                if (
                    job_creation_time + timedelta(seconds=kick_timeout * 60)
                    > new_timeout
                ):
                    continue
            job_context["timeout"] = new_timeout
            job = context.job_queue.run_once(job_func, new_timeout, context=job_context)


def _get_current_settings_helper(chat_id, settings):
    with session_scope() as session:
        chat = session.query(Chat).filter(Chat.id == chat_id).first()
        if settings == constants.Actions.get_current_intro_settings:
            return constants.get_intro_settings_message.format(**chat.__dict__)
        else:
            return constants.get_kick_settings_message.format(**chat.__dict__)


# todo rework into callback folder
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = json.loads(query.data)

    if data["action"] == constants.Actions.start_select_chat:
        user_id = query.from_user.id
        user_chats = get_chats_list(user_id, context)

        if len(user_chats) == 0:
            update.message.reply_text("У вас нет доступных чатов.")
            return

        reply_markup = InlineKeyboardMarkup(
            create_chats_list_keyboard(user_chats, context, user_id)
        )
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
                    "Приветствия",
                    callback_data=json.dumps(
                        {
                            "chat_id": selected_chat_id,
                            "action": constants.Actions.set_intro_settings,
                        }
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "Удаление и блокировка",
                    callback_data=json.dumps(
                        {
                            "chat_id": selected_chat_id,
                            "action": constants.Actions.set_kick_bans_settings,
                        }
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "Назад к списку чатов",
                    callback_data=json.dumps(
                        {
                            "chat_id": selected_chat_id,
                            "action": constants.Actions.back_to_chats,
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
    elif data["action"] == constants.Actions.set_intro_settings:
        selected_chat_id = data["chat_id"]
        keyboard = [
            [
                InlineKeyboardButton(
                    "Посмотреть текущие настройки",
                    callback_data=json.dumps(
                        {
                            "chat_id": selected_chat_id,
                            "action": constants.Actions.get_current_intro_settings,
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
                    "Изменить сообщение после представления",
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
                    "Изменить время напоминания",
                    callback_data=json.dumps(
                        {
                            "chat_id": selected_chat_id,
                            "action": constants.Actions.set_notify_timeout,
                        }
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "Изменить сообщение для обновления #whois",
                    callback_data=json.dumps(
                        {
                            "chat_id": selected_chat_id,
                            "action": constants.Actions.set_on_introduce_message_update,
                        }
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "Назад",
                    callback_data=json.dumps(
                        {
                            "chat_id": selected_chat_id,
                            "action": constants.Actions.select_chat,
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

    elif data["action"] == constants.Actions.set_kick_bans_settings:
        selected_chat_id = data["chat_id"]
        keyboard = [
            [
                InlineKeyboardButton(
                    "Посмотреть текущие настройки",
                    callback_data=json.dumps(
                        {
                            "chat_id": selected_chat_id,
                            "action": constants.Actions.get_current_kick_settings,
                        }
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "Изменить время до удаления",
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
                    "Изменить сообщение после удаления",
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
                    "Назад",
                    callback_data=json.dumps(
                        {
                            "chat_id": selected_chat_id,
                            "action": constants.Actions.select_chat,
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

    elif data["action"] == constants.Actions.back_to_chats:
        user_id = query.message.chat_id
        user_chats = list(get_chats_list(user_id, context))
        reply_markup = InlineKeyboardMarkup(
            create_chats_list_keyboard(user_chats, context, user_id)
        )
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
        constants.Actions.set_notify_timeout,
    ]:
        context.bot.edit_message_text(
            text="Отправьте новое значение",
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )
        context.user_data["chat_id"] = data["chat_id"]
        context.user_data["action"] = data["action"]

    elif data["action"] == constants.Actions.get_current_intro_settings:
        keyboard = [
            [
                InlineKeyboardButton(
                    "Назад",
                    callback_data=json.dumps(
                        {
                            "chat_id": data["chat_id"],
                            "action": constants.Actions.set_intro_settings,
                        }
                    ),
                ),
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.edit_message_text(
            text=_get_current_settings_helper(data["chat_id"], data["action"]),
            parse_mode=ParseMode.MARKDOWN,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            reply_markup=reply_markup,
        )

        context.user_data["action"] = None

    elif data["action"] == constants.Actions.get_current_kick_settings:
        keyboard = [
            [
                InlineKeyboardButton(
                    "Назад",
                    callback_data=json.dumps(
                        {
                            "chat_id": data["chat_id"],
                            "action": constants.Actions.set_kick_bans_settings,
                        }
                    ),
                ),
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.edit_message_text(
            text=_get_current_settings_helper(data["chat_id"], data["action"]),
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
            _job_rescheduling_helper(on_kick_timeout, timeout, context, chat_id)

            keyboard = [
                [
                    InlineKeyboardButton(
                        "Back",
                        callback_data=json.dumps(
                            {
                                "chat_id": chat_id,
                                "action": constants.Actions.set_kick_bans_settings,
                            }
                        ),
                    ),
                ],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(
                constants.on_success_set_kick_timeout_response,
                reply_markup=reply_markup,
            )

        elif action == constants.Actions.set_notify_timeout:
            message = update.message.text
            try:
                timeout = int(message)
                assert timeout >= 0
            except:
                update.message.reply_text(constants.on_failed_set_kick_timeout_response)
                return
            with session_scope() as sess:
                chat = Chat(id=chat_id, notify_timeout=timeout)
                sess.merge(chat)
            context.user_data["action"] = None
            _job_rescheduling_helper(on_notify_timeout, timeout, context, chat_id)

            keyboard = [
                [
                    InlineKeyboardButton(
                        "Назад",
                        callback_data=json.dumps(
                            {
                                "chat_id": chat_id,
                                "action": constants.Actions.set_intro_settings,
                            }
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
            constants.Actions.set_whois_length,
            constants.Actions.set_on_introduce_message_update,
        ]:
            message = update.message.text_markdown
            with session_scope() as sess:
                if action == constants.Actions.set_on_new_chat_member_message_response:
                    chat = Chat(id=chat_id, on_new_chat_member_message=message)
                if (
                    action
                    == constants.Actions.set_on_known_new_chat_member_message_response
                ):
                    chat = Chat(
                        id=chat_id, on_known_new_chat_member_message=message
                    )  # i
                if (
                    action == constants.Actions.set_on_successful_introducion_response
                ):  # i
                    chat = Chat(id=chat_id, on_introduce_message=message)
                if action == constants.Actions.set_notify_message:
                    chat = Chat(id=chat_id, notify_message=message)
                if action == constants.Actions.set_on_kick_message:
                    chat = Chat(id=chat_id, on_kick_message=message)
                if action == constants.Actions.set_whois_length:
                    try:
                        whois_length = int(message)
                        assert whois_length >= 0
                        chat = Chat(id=chat_id, whois_length=whois_length)
                    except:
                        update.message.reply_text(
                            constants.on_failed_set_kick_timeout_response
                        )
                        return

                if action == constants.Actions.set_on_introduce_message_update:
                    chat = Chat(id=chat_id, on_introduce_message_update=message)
                sess.merge(chat)

            if action == constants.Actions.set_on_kick_message:
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "Back",
                            callback_data=json.dumps(
                                {
                                    "chat_id": chat_id,
                                    "action": constants.Actions.set_kick_bans_settings,
                                }
                            ),
                        ),
                    ],
                ]
            else:
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "Back",
                            callback_data=json.dumps(
                                {
                                    "chat_id": chat_id,
                                    "action": constants.Actions.set_intro_settings,
                                }
                            ),
                        ),
                    ],
                ]
            context.user_data["action"] = None

            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(
                constants.on_set_new_message, reply_markup=reply_markup
            )
