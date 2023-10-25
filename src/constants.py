from enum import IntEnum, auto

# MESSAGES
on_set_new_message = "Обновил сообщение."
on_success_set_kick_timeout_response = "Обновил время до удаления."
on_sucess_set_notify_timeout_response = "Обновил время до напоминания."
on_failed_set_kick_timeout_response = "Время должно быть целым положительным числом."
on_failed_set_whois_length_response = "Длина должна быть целым положительным числом."
on_failed_kick_response = "Я не справился."
on_success_kick_response = "%USER\_MENTION% не представился и был кикнут из чата."
on_success_notify_response = "Обновил время до напоминания."
on_start_command = "Выберите чат:"
skip_on_new_chat_member_message = "%SKIP%"
help_message = """Привет! Я - бот Вахтер. Я слежу, чтобы в твоем чате были только представившиеся пользователи. Для начала работы добавь меня в чат и сделай меня администратором.
После этого для настройки бота тебе нужно написать мне в личных сообщениях /start.
По умолчанию я не удаляю из чата непредставившихся, а лишь записываю все сообщения с хэштегом #whois.
Если ты хочешь автоматически удалять непредставившихся, то установи время ожидания до удаления из чата в значение больше нуля (в минутах).
По умолчанию за 10 минут до удаления я отправляю сообщение с напоминанием.
"""
on_add_bot_to_chat_message = "Привет, я Вахтёр. Я буду следить за тем, чтобы все люди в чате были представившимися. Дайте мне админские права, чтобы я мог это делать."
on_make_admin_message = "Спасибо, теперь я могу видеть сообщения. Пожалуйста, представьтесь используя хэштег #whois"
on_make_admin_direct_message = "Есть новый чат {chat_name}"
on_introduce_message_update = (
    "Если вы хотите обновить, то добавьте тег #update к сообщению"
)

get_intro_settings_message = """
---
Сообщение для нового участника чата: {on_new_chat_member_message}
---
Сообщение при перезаходе в чат: {on_known_new_chat_member_message}
---
Сообщение после успешного представления: {on_introduce_message}
---
Сообщение напоминания: {notify_message}
---
Длина #whois: {whois_length}
---
Время до напоминания в минутах (целое положительное число): {notify_timeout}
"""

get_kick_settings_message = """
---
Время до удаления в минутах (целое положительное число): {kick_timeout}
---
Сообщение после удаления: {on_kick_message}
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
