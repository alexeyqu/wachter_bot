from enum import IntEnum, auto
import json, os


default_kick_timeout_m = 1440  # 24h in minutes
default_notify_timeout_m = 1380  # 23h in minutes
default_delete_message_timeout_m = 60  # 1h in minutes
default_whois_length = 60


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


DEBUG = os.environ.get("DEBUG", 'True') in ['True']
TEAM_TELEGRAM_IDS = json.loads(os.environ.get("TEAM_TELEGRAM_IDS", "[]"))
