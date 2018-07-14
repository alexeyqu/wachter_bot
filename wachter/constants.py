from enum import IntEnum, auto

# MESSAGES
on_set_new_message = 'Обновил сообщение.'
on_success_set_kick_timeout_response = 'Обновил таймаут кика.'
on_failed_set_kick_timeout_response = 'Таймаут должен быть целым положительным числом'
on_failed_kick_response = 'Я не справился.'
on_start_command = 'Выберите чат и действие:'

help_message = '''Привет. Для начала работы добавь меня в чат.
Для настройки бота нужно представиться в чате и написать мне в личных сообщениях.
По умолчанию я не кикаю непредставившихся, а лишь записываю все сообщения с тегом #whois.
Если нужно кикать, то установи таймаут кика в значение больше нуля (в минутах).
За 5 минут до кика я отправляю сообщение с напоминанием.
'''

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
"""

default_kick_timeout = 0
notify_delta = 5


# ACTIONS
class Actions(IntEnum):
    select_chat = auto()
    set_on_new_chat_member_message_response = auto()
    set_notify_message = auto()
    set_on_successful_introducion_response = auto()
    set_on_known_new_chat_member_message_response = auto()
    set_kick_timeout = auto()
    get_current_settings = auto()
