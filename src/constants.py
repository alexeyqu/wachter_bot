from enum import IntEnum, auto


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
