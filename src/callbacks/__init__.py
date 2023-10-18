from src.utils.button import Button
from src.handlers.admin.menu_handler import (
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

callback_map = {
    Button.SET_KICK_SETTINGS: handle_set_kick_settings,
    Button.BACK_TO_KICKS: handle_set_kick_settings,
    Button.BACK_TO_INTRO_SETTINGS: handle_intro_settings,
    Button.BACK_TO_CHATS: handle_chats_list,
    Button.BACK_TO_SETTINGS: handle_settings,
    Button.SET_INTRO_SETTINGS: handle_intro_settings,
    Button.SEE_CURRENT_INTRO_SETTINGS: handle_current_intro_settings,
}

actions_map = {
    Button.SET_WELCOME_MESSAGE: handle_set_welcome_message,
    Button.SET_WHOIS_LENGTH: handle_whois_length,
    Button.SET_REWELCOME_MESSAGE: handle_set_rewelcome_message,
    Button.SET_WARNING_TIME: handle_set_warning_time,
    Button.SET_WARNING_MESSAGE: handle_set_warning_message,
    Button.SET_THX_MESSAGE: handle_set_thx_message,
    Button.SET_AFTER_KICK_MESSAGE: handle_after_kick_message,
    Button.SET_KICK_TIMEOUT: handle_set_kick_timeout,
}
