import json
from telegram import InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from datetime import datetime, timedelta
from typing import Callable, Optional

from sqlalchemy import select

from src import constants
from src.model import Chat, session_scope
from src.texts import _

from src.handlers.group.group_handler import on_kick_timeout, on_notify_timeout

from .utils import (
    get_chats_list,
    create_chats_list_keyboard,
    new_button,
    new_keyboard_layout,
    get_chat_name,
)

from src.logging import tg_logger


async def _job_rescheduling_helper(
    job_func: Callable, timeout: int, context: ContextTypes.DEFAULT_TYPE, chat_id: int
) -> None:
    """
    This function helps in rescheduling a job in the Telegram bot's job queue.

    Args:
    job_func (Callable): The function that is to be scheduled as a job. This is the callback function that is executed when the job runs.
    timeout (int): The amount of time (in minutes) after which the job should be executed.
    context (ContextTypes.DEFAULT_TYPE): The callback context as provided by the Telegram API. This provides a context containing information about the current state of the bot and the update it is handling.
    chat_id (int): The unique identifier for the chat. This is used to query the database for chat-specific settings.

    Returns:
    None: This function does not return anything.
    """
    # Iterating through all the jobs currently in the job queue
    for job in context.job_queue.jobs():
        # If the job's name matches the name of the job function provided
        if job.name == job_func.__name__:
            # Extracting the job context and calculating the new timeout
            job_data = job.data
            job_creation_time = datetime.fromtimestamp(job_data.get("creation_time"))
            new_timeout = job_creation_time + timedelta(seconds=timeout * 60)

            # If the new timeout is in the past, set it to now
            if new_timeout < datetime.now():
                new_timeout = datetime.now()

            # Schedule the current job for removal
            job.schedule_removal()

            # If the job is a notification timeout, perform additional checks
            if job_func == on_notify_timeout:
                # Querying the database to get the chat's kick timeout setting
                async with session_scope() as sess:
                    result = await sess.execute(select(Chat).filter(Chat.id == chat_id))
                    chat: Optional[Chat] = result.scalars().first()
                    kick_timeout = chat.kick_timeout if chat else 0

                # If the new timeout is greater than the kick timeout, skip to the next job
                if (
                    job_creation_time + timedelta(seconds=kick_timeout * 60)
                ) > new_timeout:
                    continue

            # Update the job context with the new timeout
            job_data["timeout"] = new_timeout

            # Schedule the new job with the updated context and timeout
            job = context.job_queue.run_once(job_func, new_timeout, data=job_data)


async def _get_current_settings_helper(
    chat_id: int, settings: str, chat_name: str
) -> str:
    """
    Retrieve the current settings for a specific chat based on the settings category provided.
    This function is now an asynchronous function.

    Args:
    chat_id (int): The ID of the chat for which the settings are to be retrieved.
    settings (str): A string indicating the category of settings to retrieve.

    Returns:
    str: A formatted message string containing the current settings.
    """
    async with session_scope() as session:
        result = await session.execute(select(Chat).filter(Chat.id == chat_id))
        chat: Optional[Chat] = result.scalars().first()

        if settings == constants.Actions.get_current_intro_settings:
            print("Loading intro settings for chat_id:", chat_id)
            return (
                _("msg__get_intro_settings")
                .format(chat_name=chat_name, **chat.__dict__)
                .replace("%USER\\_MENTION%", "%USER_MENTION%")
            )
        else:
            return (
                _("msg__get_kick_settings")
                .format(chat_name=chat_name, **chat.__dict__)
                .replace("%USER\\_MENTION%", "%USER_MENTION%")
            )


# todo rework into callback folder
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle button presses in the Telegram bot's inline keyboard.

    Args:
    update (Update): The Telegram update object.
    context (ContextTypes.DEFAULT_TYPE): The callback context as provided by the Telegram API.

    Returns:
    None
    """
    query = update.callback_query
    data = json.loads(query.data)

    if data["action"] == constants.Actions.start_select_chat:
        user_id = query.from_user.id
        user_chats = await get_chats_list(user_id, context)
        if len(user_chats) == 0:
            await update.message.reply_text(_("msg__no_chats_available"))
            return
        reply_markup = InlineKeyboardMarkup(
            await create_chats_list_keyboard(user_chats, context, user_id)
        )
        await context.bot.edit_message_text(
            _("msg__start_command"),
            reply_markup=reply_markup,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )

    if data["action"] == constants.Actions.select_chat:
        selected_chat_id = data["chat_id"]
        button_configs = [
            [{"text": _("btn__intro"), "action": constants.Actions.set_intro_settings}],
            [
                {
                    "text": _("btn__kicks"),
                    "action": constants.Actions.set_kick_bans_settings,
                }
            ],
            [
                {
                    "text": _("btn__back_to_chats"),
                    "action": constants.Actions.back_to_chats,
                }
            ],
        ]
        reply_markup = new_keyboard_layout(button_configs, selected_chat_id)
        chat_name = await get_chat_name(context.bot, selected_chat_id)
        await context.bot.edit_message_text(
            _("msg__select_chat").format(chat_name=chat_name),
            reply_markup=reply_markup,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )
    elif data["action"] == constants.Actions.set_intro_settings:
        selected_chat_id = data["chat_id"]
        button_configs = [
            [
                {
                    "text": _("btn__current_settings"),
                    "action": constants.Actions.get_current_intro_settings,
                }
            ],
            [
                {
                    "text": _("btn__change_welcome_message"),
                    "action": constants.Actions.set_on_new_chat_member_message_response,
                }
            ],
            [
                {
                    "text": _("btn__change_rewelcome_message"),
                    "action": constants.Actions.set_on_known_new_chat_member_message_response,
                }
            ],
            [
                {
                    "text": _("btn__change_notify_message"),
                    "action": constants.Actions.set_notify_message,
                }
            ],
            [
                {
                    "text": _("btn__change_sucess_message"),
                    "action": constants.Actions.set_on_successful_introducion_response,
                }
            ],
            [
                {
                    "text": _("btn__change_notify_timeout"),
                    "action": constants.Actions.set_notify_timeout,
                }
            ],
            [
                {
                    "text": _("btn__change_whois_length"),
                    "action": constants.Actions.set_whois_length,
                }
            ],
            [
                {
                    "text": _("btn__change_whois_message"),
                    "action": constants.Actions.set_on_introduce_message_update,
                }
            ],
            [{"text": _("btn__back"), "action": constants.Actions.select_chat}],
        ]
        reply_markup = new_keyboard_layout(button_configs, selected_chat_id)
        await context.bot.edit_message_reply_markup(
            reply_markup=reply_markup,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )

    elif data["action"] == constants.Actions.set_kick_bans_settings:
        selected_chat_id = data["chat_id"]
        button_configs = [
            [
                {
                    "text": _("btn__current_settings"),
                    "action": constants.Actions.get_current_kick_settings,
                }
            ],
            [
                {
                    "text": _("btn__change_kick_timeout"),
                    "action": constants.Actions.set_kick_timeout,
                }
            ],
            [
                {
                    "text": _("btn__change_kick_message"),
                    "action": constants.Actions.set_on_kick_message,
                }
            ],
            [{"text": _("btn__back"), "action": constants.Actions.select_chat}],
        ]
        reply_markup = new_keyboard_layout(button_configs, selected_chat_id)
        await context.bot.edit_message_reply_markup(
            reply_markup=reply_markup,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )

    elif data["action"] == constants.Actions.back_to_chats:
        user_id = query.message.chat_id
        user_chats = await get_chats_list(user_id, context)
        reply_markup = InlineKeyboardMarkup(
            await create_chats_list_keyboard(user_chats, context, user_id)
        )
        await context.bot.edit_message_text(
            _("msg__start_command"),
            reply_markup=reply_markup,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )

    elif data["action"] == constants.Actions.set_on_new_chat_member_message_response:
        await context.bot.edit_message_text(
            text=_("msg__set_new_welcome_message"),
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            parse_mode=ParseMode.MARKDOWN,
        )
        context.user_data["chat_id"] = data["chat_id"]
        context.user_data["action"] = data["action"]

    elif data["action"] == constants.Actions.set_kick_timeout:
        await context.bot.edit_message_text(
            text=_("msg__set_new_kick_timout"),
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )
        context.user_data["chat_id"] = data["chat_id"]
        context.user_data["action"] = data["action"]

    elif (
        data["action"]
        == constants.Actions.set_on_known_new_chat_member_message_response
    ):
        await context.bot.edit_message_text(
            text=_("msg__set_new_rewelcome_message"),
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            parse_mode=ParseMode.MARKDOWN,
        )
        context.user_data["chat_id"] = data["chat_id"]
        context.user_data["action"] = data["action"]

    elif data["action"] == constants.Actions.set_notify_message:
        await context.bot.edit_message_text(
            text=_("msg__set_new_notify_message"),
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            parse_mode=ParseMode.MARKDOWN,
        )
        context.user_data["chat_id"] = data["chat_id"]
        context.user_data["action"] = data["action"]

    elif data["action"] == constants.Actions.set_on_new_chat_member_message_response:
        await context.bot.edit_message_text(
            text=_("msg__set_new_welcome_message"),
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            parse_mode=ParseMode.MARKDOWN,
        )
        context.user_data["chat_id"] = data["chat_id"]
        context.user_data["action"] = data["action"]

    elif data["action"] == constants.Actions.set_on_successful_introducion_response:
        await context.bot.edit_message_text(
            text=_("msg__set_new_sucess_message"),
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            parse_mode=ParseMode.MARKDOWN,
        )
        context.user_data["chat_id"] = data["chat_id"]
        context.user_data["action"] = data["action"]

    elif data["action"] == constants.Actions.set_whois_length:
        await context.bot.edit_message_text(
            text=_("msg__set_new_whois_length"),
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )
        context.user_data["chat_id"] = data["chat_id"]
        context.user_data["action"] = data["action"]

    elif data["action"] == constants.Actions.set_on_kick_message:
        await context.bot.edit_message_text(
            text=_("msg__set_new_kick_message"),
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            parse_mode=ParseMode.MARKDOWN,
        )
        context.user_data["chat_id"] = data["chat_id"]
        context.user_data["action"] = data["action"]

    elif data["action"] == constants.Actions.set_notify_timeout:
        await context.bot.edit_message_text(
            text=_("msg__set_new_notify_timeout"),
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )
        context.user_data["chat_id"] = data["chat_id"]
        context.user_data["action"] = data["action"]

    elif data["action"] == constants.Actions.set_on_introduce_message_update:
        await context.bot.edit_message_text(
            text=_("msg__set_new_whois_message"),
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            parse_mode=ParseMode.MARKDOWN,
        )
        context.user_data["chat_id"] = data["chat_id"]
        context.user_data["action"] = data["action"]

    elif data["action"] == constants.Actions.get_current_intro_settings:
        keyboard = [
            [
                new_button(
                    _("btn__back"),
                    data["chat_id"],
                    constants.Actions.set_intro_settings,
                )
            ]
        ]
        chat_name = await get_chat_name(context.bot, data["chat_id"])
        reply_markup = InlineKeyboardMarkup(keyboard)
        settings = await _get_current_settings_helper(
            data["chat_id"], data["action"], chat_name
        )
        await context.bot.edit_message_text(
            text=settings,
            parse_mode=ParseMode.MARKDOWN,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            reply_markup=reply_markup,
        )

        context.user_data["action"] = None

    elif data["action"] == constants.Actions.get_current_kick_settings:
        keyboard = [
            [
                new_button(
                    _("btn__back"),
                    data["chat_id"],
                    constants.Actions.set_kick_bans_settings,
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        chat_name = await get_chat_name(context.bot, data["chat_id"])
        settings = await _get_current_settings_helper(
            data["chat_id"], data["action"], chat_name
        )
        await context.bot.edit_message_text(
            text=settings,
            parse_mode=ParseMode.MARKDOWN,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            reply_markup=reply_markup,
        )

        context.user_data["action"] = None


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle text messages received by the Telegram bot.

    Args:
    update (Update): The Telegram update object.
    context (ContextTypes.DEFAULT_TYPE): The callback context as provided by the Telegram API.

    Returns:
    None: This function returns nothing.
    """
    chat_id = update.effective_message.chat_id

    if chat_id > 0:
        action = context.user_data.get("action")

        if action is None:
            return

        chat_id = context.user_data["chat_id"]

        if action == constants.Actions.set_kick_timeout:
            message = update.effective_message.text
            try:
                timeout = int(message)
                assert timeout >= 0
            except:
                await update.effective_message.reply_text(
                    _("msg__failed_set_kick_timeout_response")
                )
                return
            async with session_scope() as sess:
                chat = Chat(id=chat_id, kick_timeout=timeout)
                await sess.merge(chat)
            context.user_data["action"] = None
            await _job_rescheduling_helper(on_kick_timeout, timeout, context, chat_id)

            keyboard = [
                [
                    new_button(
                        _("btn__back"),
                        chat_id,
                        constants.Actions.set_kick_bans_settings,
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.effective_message.reply_text(
                _("msg__success_set_kick_timeout_response"),
                reply_markup=reply_markup,
            )

        elif action == constants.Actions.set_notify_timeout:
            message = update.effective_message.text
            try:
                timeout = int(message)
                assert timeout >= 0
            except:
                await update.effective_message.reply_text(_("msg__failed_kick_response"))
                return
            async with session_scope() as sess:
                chat = Chat(id=chat_id, notify_timeout=timeout)
                await sess.merge(chat)
            context.user_data["action"] = None
            await _job_rescheduling_helper(on_notify_timeout, timeout, context, chat_id)

            keyboard = [
                [
                    new_button(
                        _("btn__back"), chat_id, constants.Actions.set_intro_settings
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.effective_message.reply_text(
                _("msg__sucess_set_notify_timeout_response"),
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
            message = update.effective_message.text_markdown
            reply_message = _("msg__set_new_message")
            async with session_scope() as sess:
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
                if action == constants.Actions.set_whois_length:
                    try:
                        whois_length = int(message)
                        assert whois_length >= 0
                        chat = Chat(id=chat_id, whois_length=whois_length)
                        reply_message = _("msg__sucess_whois_length")
                    except:
                        await update.effective_message.reply_text(_("msg__failed_whois_response"))
                        return

                if action == constants.Actions.set_on_introduce_message_update:
                    if (
                        "#update"
                        not in update.effective_message.parse_entities(types=["hashtag"]).values()
                    ):
                        await update.effective_message.reply_text(
                            _("msg__need_hashtag_update_response")
                        )
                        return
                    chat = Chat(id=chat_id, on_introduce_message_update=message)
                await sess.merge(chat)

            if action in [
                constants.Actions.set_on_kick_message,
                constants.Actions.set_kick_timeout,
            ]:
                keyboard = [
                    [
                        new_button(
                            _("btn__back"),
                            chat_id,
                            constants.Actions.set_kick_bans_settings,
                        )
                    ]
                ]
            else:
                keyboard = [
                    [
                        new_button(
                            _("btn__back"),
                            chat_id,
                            constants.Actions.set_intro_settings,
                        )
                    ]
                ]
            context.user_data["action"] = None

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.effective_message.reply_text(reply_message, reply_markup=reply_markup)
