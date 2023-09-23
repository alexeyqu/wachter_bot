from enum import IntEnum, auto

# MESSAGES
on_set_new_message = "Обновил сообщение."
on_success_set_kick_timeout_response = "Обновил таймаут кика."
on_failed_set_kick_timeout_response = "Таймаут должен быть целым положительным числом"
on_failed_kick_response = "Я не справился."
on_success_kick_response = "%USER\_MENTION% не представился и был кикнут из чата."
on_start_command = "Выберите чат и действие:"
skip_on_new_chat_member_message = "%SKIP%"
help_message = """Привет. Для начала работы добавь меня в чат.
Для настройки бота админу нужно представиться в чате (написать сообщение с #whois длинной больше 120 символов) и написать мне в личных сообщениях /start.
По умолчанию я не кикаю непредставившихся, а лишь записываю все сообщения с тегом #whois.
Если нужно кикать, то установи таймаут кика в значение больше нуля (в минутах).
За 10 минут до кика я отправляю сообщение с напоминанием.
"""

get_settings_message = """
Таймаут кика: {kick_timeout}
---
Сообщение для нового участника чата: {on_new_chat_member_message}
---
Сообщение при перезаходе в чат: {on_known_new_chat_member_message}
---
Сообщение после успешного представления: {on_introduce_message}
---
Сообщение предупреждения: {notify_message}
---
Сообщение после кика: {on_kick_message}
"""

default_kick_timeout = 0
notify_delta = 10
min_whois_length = 60


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
