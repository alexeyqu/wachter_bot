from enum import IntEnum, auto
import json, os


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
    "Хакер %USER_MENTION% молчит и покидает чат. ⚰",
    "Хакера %USER_MENTION% забрал роскомнадзор",
    "Хакера %USER_MENTION% забрал Интерпол",
    "Хакер %USER_MENTION% провалил дедлайн",
    "Хакер %USER_MENTION% не смог выйти из VIM",
    "Хакер %USER_MENTION% пошёл кормить рыбок",
    "Хакер %USER_MENTION% провалил испытание",
]

RH_CHAT_ID = -1001147286684

DEBUG = os.environ.get("DEBUG", True)
TEAM_TELEGRAM_IDS = json.loads(os.environ.get("TEAM_TELEGRAM_IDS", "[]"))
