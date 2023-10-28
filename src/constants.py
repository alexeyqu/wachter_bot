from enum import IntEnum, auto

# MESSAGES
on_set_new_message = "Обновил сообщение."
on_set_whois_length = "Обновил необходимую длину #whois."
on_success_set_kick_timeout_response = "Обновил время до удаления."
on_sucess_set_notify_timeout_response = "Обновил время до напоминания."
on_failed_set_kick_timeout_response = "Время должно быть целым положительным числом."
on_failed_set_whois_length_response = "Длина должна быть целым положительным числом."
need_hashtag_update_response = "Сообщение должно содержать #update."
on_failed_kick_response = "Я не справился. Возможно, мне не хватает прав."
on_success_notify_response = "Обновил время до напоминания."
on_start_command = "Выберите чат:"
on_select_chat_message = "Выбран чат {chat_name}. Теперь выберите действие:"
skip_on_new_chat_member_message = "%SKIP%"
help_message = """Привет! Я — бот Вахтер. Я слежу, чтобы в твоем чате были только представившиеся пользователи. 
Для начала работы добавь меня в чат и сделай меня администратором.
После этого я помогу тебе настроить чат в личных сообщениях.
По умолчанию я буду удалять непредставившихся участников через сутки, а за час до этого напомню им представиться.
Если ты не хочешь автоматически удалять непредставившихся, то установи время ожидания до удаления из чата в 0.
"""
on_add_bot_to_chat_message = "Привет! Я — бот Вахтер. Я буду следить, чтобы в этом чате все пользователи были представившимися. Чтобы я мог начать работать, сделайте меня администратором."
on_make_admin_message = "Спасибо, теперь я администратор и могу видеть сообщения. Я буду добавлять в мою базу всех представившихся пользователей этого чата. Чтобы представиться, пожалуйста, напишите сообщение с хэштегом #whois и длиной не менее {whois_length} символов."
on_make_admin_direct_message = "Новый чат {chat_name}"
on_new_chat_member_message = "Добро пожаловать! Пожалуйста, представьтесь с использованием хэштега #whois и поздоровайтесь с сообществом."
on_known_new_chat_member_message = "Добро пожаловать снова!"
on_introduce_message = "Спасибо и добро пожаловать!"
on_kick_message = "%USER\_MENTION% молчит и покидает чат."
notify_message = (
    "%USER\_MENTION%, пожалуйста, представьтесь с использованием хэштега #whois."
)
on_introduce_message_update = "%USER\_MENTION%, если вы хотите обновить существующий #whois, пожалуйста добавьте тег #update к сообщению."
on_short_whois_message = "%USER\_MENTION%, напишите про себя побольше, хотя бы {whois_length} символов. Спасибо!"


get_intro_settings_message = """
Выбран чат {chat_name}.
---
Сообщение для нового участника чата: {on_new_chat_member_message}
---
Сообщение при перезаходе в чат: {on_known_new_chat_member_message}
---
Сообщение после успешного представления: {on_introduce_message}
---
Сообщение напоминания: {notify_message}
---
Необходимая длина представления с хэштегом #whois для новых пользователей: {whois_length}
---
Время до напоминания в минутах (целое положительное число): {notify_timeout}
---
Сообщение для обновления информации в #whois: {on_introduce_message_update}
"""

get_kick_settings_message = """
Выбран чат {chat_name}.
---
Время до удаления в минутах (целое положительное число): {kick_timeout}
---
Сообщение после удаления: {on_kick_message}
"""

default_kick_timeout = 1440  # 24h in minutes
default_notify_timeout = 1380  # 23h in minutes
notify_delta = 10
default_whois_length = 60
default_delete_message = 60


# ACTIONS
class Actions(IntEnum):
    start_select_chat = auto()
    select_chat = auto()
    set_on_new_chat_member_message_response = auto()
    set_notify_message = auto()
    set_on_successful_introducion_response = auto()
    set_on_known_new_chat_member_message_response = auto()
    set_kick_timeout = auto()
    set_on_kick_message = auto()
    get_current_settings = auto()
    set_intro_settings = auto()
    set_kick_bans_settings = auto()
    back_to_chats = auto()
    set_notify_timeout = auto()
    get_current_kick_settings = auto()
    get_current_intro_settings = auto()
    set_whois_length = auto()
    set_on_introduce_message_update = auto()


RH_kick_messages = [
    "Хакер %USER\_MENTION% молчит и покидает чат. ⚰",
    "Хакера %USER\_MENTION% забрал роскомнадзор",
    "Хакера %USER\_MENTION% забрал Интерпол",
    "Хакер %USER\_MENTION% провалил дедлайн",
    "Хакер %USER\_MENTION% не смог выйти из VIM",
    "Хакер %USER\_MENTION% пошёл кормить рыбок",
    "Хакер %USER\_MENTION% провалил испытание",
]

RH_CHAT_ID = -1001147286684
