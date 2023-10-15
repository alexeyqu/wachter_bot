from enum import Enum

from src.handlers.admin.menu_handler import (
    handle_select_chat,
    handle_action,
    handle_set_kick_timeout,
    handle_chats_list,
    handle_current_intro_settings,
    handle_intro_settings,
    handle_set_kick_settings,
    handle_set_thx_message,
    handle_set_warning_message,
    handle_set_warning_time,
    handle_set_welcome_message,
    handle_settings,
    handle_whois_length,
    handle_set_rewelcome_message,
    handle_after_kick_message,
)


class Button(Enum):
    SELECT_CHAT = "select_chat_placeholder"
    SET_KICK_SETTINGS = "Настройки кика"
    SET_KICK_TIMEOUT = "Изменить таймаут кика"
    CHATS_LIST = "К списку чатов"
    BACK = "Назад"


actions_map = {
    Button.SELECT_CHAT: handle_select_chat,
    Button.SET_KICK_SETTINGS: handle_set_kick_settings,  # will return a menu with SET_KICK_TIMEOUT button etc
    Button.SEE_CURRENT_KICK_SETTINGS: hanlde_see_current_kick_settings,
    Button.KICK_IF_NO_INTRO: handle_kick_if_no_intro,
    Button.SET_AFTER_KICK_MESSAGE: handle_after_kick_message,
    Button.SET_KICK_TIMEOUT: handle_set_kick_timeout,
    Button.CHATS_LIST: handle_select_chat,
    Button.BACK_TO_KICKS: handle_set_kick_settings,
    Button.BACK_TO_INTRO_SETTINGS: handle_intro_settings,
    Button.BACK_TO_CHATS: handle_chats_list,
    Button.BACK_TO_SETTINGS: handle_settings,
    Button.SET_INTRO_SETTINGS: handle_intro_settings,
    Button.SEE_CURRENT_INTRO_SETTINGS: handle_current_intro_settings,
    Button.SET_WELCOME_MESSAGE: handle_set_welcome_message,
    Button.SET_WHOIS_LENGTH: handle_whois_length,
    Button.SET_REWELCOME_MESSAGE: handle_set_rewelcome_message,
    Button.SET_WARNING_TIME: handle_set_warning_time,
    Button.SET_WARNING_MESSAGE: handle_set_warning_message,
    Button.SET_THX_MESSAGE: handle_set_thx_message,
}
