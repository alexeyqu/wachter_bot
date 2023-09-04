import json
import logging
from telegram import (
    Bot,
    Update,
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
)
from telegram.ext import Job, JobQueue
from telegram.error import TelegramError
from datetime import datetime, timedelta
from model import Chat, User, session_scope, orm_to_dict
import constants
import re
import random
import typing

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def on_error(bot: Bot, update: Update, error: TelegramError):
    logger.warning(f'Update "{update}" caused error "{error}"')


def authorize_user(bot: Bot, chat_id: int, user_id: int):
    try:
        status = bot.get_chat_member(chat_id, user_id).status
        return status in ["creator", "administrator"]
    except e:
        return False


def mention_markdown(bot: Bot, chat_id: int, user_id: int, message: Message):
    user = bot.get_chat_member(chat_id, user_id).user
    if not user.name:
        # если пользователь удален, у него пропадает имя и markdown выглядит так: (tg://user?id=666)
        user_mention_markdown = ""
    else:
        user_mention_markdown = user.mention_markdown()

    # \ нужен из-за формата сообщений в маркдауне
    return message.replace("%USER\_MENTION%", user_mention_markdown)


def on_help_command(bot: Bot, update: Update):
    update.message.reply_text(constants.help_message)


def on_skip_command(bot: Bot, update: Update, job_queue: JobQueue):
    chat_id = update.message.chat_id

    if chat_id > 0:
        return

    if not update.message:
        update.message = update.edited_message

    if update.message.reply_to_message is not None:
        user_id = update.message.reply_to_message.from_user.id

        if not authorize_user(bot, chat_id, user_id):
            return
        removed = False
        for job in job_queue.jobs():
            if (
                job.context["user_id"] == user_id
                and job.context["chat_id"] == chat_id
                and job.enabled == True
            ):
                try:
                    bot.delete_message(
                        job.context["chat_id"], job.context["message_id"]
                    )
                except:
                    pass
                job.enabled = False
                job.schedule_removal()
                removed = True
        if removed:
            update.message.reply_text(constants.on_success_skip)
    else:
        update.message.reply_text(constants.on_failed_skip)


def on_new_chat_member(bot: Bot, update: Update, job_queue: JobQueue):
    chat_id = update.message.chat_id
    user_id = update.message.new_chat_members[-1].id

    for job in job_queue.jobs():
        if (
            job.context["user_id"] == user_id
            and job.context["chat_id"] == chat_id
            and job.enabled == True
        ):
            job.enabled = False
            job.schedule_removal()

    with session_scope() as sess:
        user = (
            sess.query(User)
            .filter(User.chat_id == chat_id, User.user_id == user_id)
            .first()
        )
        chat = sess.query(Chat).filter(Chat.id == chat_id).first()

        if chat is None:
            chat = Chat(id=chat_id)
            sess.add(chat)
            sess.commit()

        if user is not None:
            update.message.reply_text(chat.on_known_new_chat_member_message)
            return

        message = chat.on_new_chat_member_message
        timeout = chat.kick_timeout

    if message == constants.skip_on_new_chat_member_message:
        return

    message_markdown = mention_markdown(bot, chat_id, user_id, message)
    msg = update.message.reply_text(message_markdown, parse_mode=ParseMode.MARKDOWN)

    if timeout != 0:
        if timeout >= 10:
            job = job_queue.run_once(
                on_notify_timeout,
                (timeout - constants.notify_delta) * 60,
                context={
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "job_queue": job_queue,
                },
            )

        job = job_queue.run_once(
            on_kick_timeout,
            timeout * 60,
            context={
                "chat_id": chat_id,
                "user_id": user_id,
                "message_id": msg.message_id,
            },
        )


def on_notify_timeout(bot: Bot, job: Job):
    with session_scope() as sess:
        chat = sess.query(Chat).filter(Chat.id == job.context["chat_id"]).first()

        message_markdown = mention_markdown(
            bot, job.context["chat_id"], job.context["user_id"], chat.notify_message
        )

        message = bot.send_message(
            job.context["chat_id"], text=message_markdown, parse_mode=ParseMode.MARKDOWN
        )

        job.context["job_queue"].run_once(
            delete_message,
            constants.notify_delta * 60,
            context={
                "chat_id": job.context["chat_id"],
                "user_id": job.context["user_id"],
                "message_id": message.message_id,
            },
        )


def delete_message(bot: Bot, job: Job):
    logger.info("delete called")
    try:
        bot.delete_message(job.context["chat_id"], job.context["message_id"])
        logger.info("delete sucess")
    except:
        logger.info("suck")
        print(f"can't delete {job.context['message_id']} from {job.context['chat_id']}")


def on_kick_timeout(bot: Bot, job: Job):
    try:
        bot.delete_message(job.context["chat_id"], job.context["message_id"])
    except:
        pass

    try:
        bot.kick_chat_member(
            job.context["chat_id"],
            job.context["user_id"],
            until_date=datetime.now() + timedelta(seconds=60),
        )

        with session_scope() as sess:
            chat = sess.query(Chat).filter(Chat.id == job.context["chat_id"]).first()

            if chat.on_kick_message.lower() not in ["false", "0"]:
                message_markdown = mention_markdown(
                    bot,
                    job.context["chat_id"],
                    job.context["user_id"],
                    chat.on_kick_message,
                )
                if job.context["chat_id"] == constants.RH_CHAT_ID:
                    message_markdown = mention_markdown(
                        bot,
                        job.context["chat_id"],
                        job.context["user_id"],
                        random.choice(constants.RH_kick_messages),
                    )
                bot.send_message(
                    job.context["chat_id"],
                    text=message_markdown,
                    parse_mode=ParseMode.MARKDOWN,
                )
    except Exception as e:
        logging.error(e)
        bot.send_message(job.context["chat_id"], text=constants.on_failed_kick_response)


def on_hashtag_message(bot: Bot, update: Update, user_data: dict, job_queue: JobQueue):
    if not update.message:
        update.message = update.edited_message

    chat_id = update.message.chat_id

    if (
        "#whois" in update.message.parse_entities(types=["hashtag"]).values()
        and len(update.message.text) >= constants.min_whois_length
        and chat_id < 0
    ):
        user_id = update.message.from_user.id

        with session_scope() as sess:
            chat = sess.query(Chat).filter(Chat.id == chat_id).first()

            if chat is None:
                chat = Chat(id=chat_id)
                sess.add(chat)
                sess.commit()

            message = chat.on_introduce_message

        with session_scope() as sess:
            user = User(chat_id=chat_id, user_id=user_id, whois=update.message.text)
            sess.merge(user)

        removed = False
        for job in job_queue.jobs():
            if (
                job.context["user_id"] == user_id
                and job.context["chat_id"] == chat_id
                and job.enabled == True
            ):
                try:
                    bot.delete_message(
                        job.context["chat_id"], job.context["message_id"]
                    )
                except:
                    pass
                job.enabled = False
                job.schedule_removal()
                removed = True

        if removed:
            message_markdown = mention_markdown(bot, chat_id, user_id, message)
            update.message.reply_text(message_markdown, parse_mode=ParseMode.MARKDOWN)

    else:
        on_message(bot, update, user_data=user_data, job_queue=job_queue)


def get_chats(users: list, user_id: int, bot: Bot):
    for x in users:
        try:
            if authorize_user(bot, x.chat_id, user_id):
                yield {
                    "title": bot.get_chat(x.chat_id).title or x.chat_id,
                    "id": x.chat_id,
                }
        except Exception:
            pass


def on_start_command(bot: Bot, update: Update, user_data: dict):
    user_id = update.message.chat_id

    if user_id < 0:
        return

    with session_scope() as sess:
        users = sess.query(User).filter(User.user_id == user_id)
        user_chats = list(get_chats(users, user_id, bot))

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
        if authorize_user(bot, chat["id"], user_id)
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(constants.on_start_command, reply_markup=reply_markup)


def on_button_click(bot: Bot, update: Update, user_data: dict):
    query = update.callback_query
    data = json.loads(query.data)

    if data["action"] == constants.Actions.start_select_chat:
        with session_scope() as sess:
            user_id = query.from_user.id
            users = sess.query(User).filter(User.user_id == user_id)
            user_chats = [
                {"title": bot.get_chat(x.chat_id).title or x.chat_id, "id": x.chat_id}
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
            if authorize_user(bot, chat["id"], user_id)
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_reply_markup(
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
                    "Изменить regex для фильтра сообщений",
                    callback_data=json.dumps(
                        {
                            "chat_id": selected_chat_id,
                            "action": constants.Actions.set_regex_filter,
                        }
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "Изменить фильтрацию только для новых пользователей",
                    callback_data=json.dumps(
                        {
                            "chat_id": selected_chat_id,
                            "action": constants.Actions.set_filter_only_new_users,
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
        bot.edit_message_reply_markup(
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
        constants.Actions.set_regex_filter,
        constants.Actions.set_filter_only_new_users,
    ]:
        bot.edit_message_text(
            text="Отправьте новое значение",
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )
        user_data["chat_id"] = data["chat_id"]
        user_data["action"] = data["action"]

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
            bot.edit_message_text(
                text=constants.get_settings_message.format(**chat.__dict__),
                parse_mode=ParseMode.MARKDOWN,
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                reply_markup=reply_markup,
            )

        user_data["action"] = None


def filter_message(chat_id: int, message: Message):
    if not message:
        return False

    with session_scope() as sess:
        chat = sess.query(Chat).filter(Chat.id == chat_id).first()

        if chat.regex_filter is None:
            return False
        else:
            return re.search(chat.regex_filter, message)


def on_forward(bot: Bot, update: Update, job_queue: JobQueue):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    removed = False

    if chat_id < 0 and not authorize_user(bot, chat_id, user_id):
        with session_scope() as sess:
            chat = sess.query(Chat).filter(Chat.id == chat_id == chat_id).first()
            if chat.regex_filter is None:
                return

        for job in job_queue.jobs():
            if (
                job.context["user_id"] == user_id
                and job.context["chat_id"] == chat_id
                and job.enabled == True
            ):
                removed = True
                try:
                    bot.delete_message(
                        job.context["chat_id"], job.context["message_id"]
                    )
                except:
                    pass
                job.enabled = False
                job.schedule_removal()

        if removed:
            bot.delete_message(chat_id, update.message.message_id)
            message_markdown = mention_markdown(
                bot, chat_id, user_id, constants.on_filtered_message
            )
            message = bot.send_message(
                chat_id, text=message_markdown, parse_mode=ParseMode.MARKDOWN
            )
            bot.kick_chat_member(
                chat_id, user_id, until_date=datetime.now() + timedelta(seconds=60)
            )


def is_new_user(chat_id: int, user_id: int):
    with session_scope() as sess:
        #  if user is not in database he hasn't introduced himself with #whois
        user = (
            sess.query(User)
            .filter(User.user_id == user_id, User.chat_id == chat_id)
            .first()
        )
        is_new = not user
        return is_new


def is_chat_filters_new_users(chat_id: int):
    with session_scope() as sess:
        filter_only_new_users = (
            sess.query(Chat.filter_only_new_users).filter(Chat.id == chat_id).first()
        )
        return filter_only_new_users


def on_message(bot: Bot, update: Update, user_data: dict, job_queue: JobQueue):
    if not update.message:
        update.message = update.edited_message

    chat_id = update.message.chat_id

    if chat_id < 0:
        user_id = update.message.from_user.id
        if update.message.forward_from:
            on_forward(bot, update, job_queue)
            return

        message_text = update.message.text or update.message.caption
        filter_mask = not authorize_user(bot, chat_id, user_id) and filter_message(
            chat_id, message_text
        )

        if is_chat_filters_new_users(chat_id):
            filter_mask = filter_mask and is_new_user(chat_id, user_id)

        if filter_mask:
            bot.delete_message(chat_id, update.message.message_id)
            message_markdown = mention_markdown(
                bot, chat_id, user_id, constants.on_filtered_message
            )
            for job in job_queue.jobs():
                if (
                    job.context["user_id"] == user_id
                    and job.context["chat_id"] == chat_id
                    and job.enabled == True
                ):
                    try:
                        bot.delete_message(
                            job.context["chat_id"], job.context["message_id"]
                        )
                    except:
                        pass
                    job.enabled = False
                    job.schedule_removal()
            message = bot.send_message(
                chat_id, text=message_markdown, parse_mode=ParseMode.MARKDOWN
            )
            bot.kick_chat_member(
                chat_id, user_id, until_date=datetime.now() + timedelta(seconds=60)
            )
    else:
        user_id = chat_id
        action = user_data.get("action")

        if action is None:
            return

        chat_id = user_data["chat_id"]

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
            user_data["action"] = None

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
            constants.Actions.set_regex_filter,
            constants.Actions.set_filter_only_new_users,
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
                if action == constants.Actions.set_filter_only_new_users:
                    if message.lower() in ["true", "1"]:
                        filter_only_new_users = True
                    else:
                        filter_only_new_users = False
                    chat = Chat(id=chat_id, filter_only_new_users=filter_only_new_users)

                if action == constants.Actions.set_regex_filter:
                    if message == "%TURN_OFF%":
                        chat = Chat(id=chat_id, regex_filter=None)
                    else:
                        message = update.message.text
                        chat = Chat(id=chat_id, regex_filter=message)
                sess.merge(chat)

            user_data["action"] = None

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


def on_whois_command(bot: Bot, update: Update, args: list):
    if len(args) != 1:
        update.message.reply_text("Usage: /whois <user_id>")

    chat_id = update.message.chat_id
    user_id = args[0]  # TODO: Use username instead of user_id

    with session_scope() as sess:
        user = (
            sess.query(User)
            .filter(User.chat_id == chat_id, User.user_id == user_id)
            .first()
        )

        if user is None:
            update.message.reply_text("user not found")
            return

        update.message.reply_text(f"whois: {user.whois}")
