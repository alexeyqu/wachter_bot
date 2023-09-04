from telegram.ext import (
    Updater,
    CommandHandler,
    Filters,
    MessageHandler,
    CallbackQueryHandler,
)
from custom_filters import filter_bot_added
import actions
import logging
from logging import config
import os


log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "telegram": {
            "class": "telegram_logger.TelegramHandler",
            "token": os.environ["TELEGRAM_TOKEN"],
            "chat_ids": [os.environ["TELEGRAM_ERROR_CHAT_ID"]],
        }
    },
    "loggers": {
        "telegram": {
            "level": "INFO",
            "handlers": ["telegram",]
        }
    }
}

config.dictConfig(log_config)
logger = logging.getLogger("telegram")


def main():
    updater = Updater(os.environ["TELEGRAM_TOKEN"])
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("help", actions.on_help_command))
    dp.add_error_handler(actions.on_error)

    dp.add_handler(
        MessageHandler(
            Filters.status_update.new_chat_members & filter_bot_added,
            actions.on_new_chat_member,
            pass_job_queue=True,
        )
    )
    dp.add_handler(
        MessageHandler(
            Filters.entity("hashtag"),
            actions.on_hashtag_message,
            pass_job_queue=True,
            edited_updates=True,
            pass_user_data=True,
        )
    )
    dp.add_handler(
        MessageHandler(Filters.forwarded, actions.on_forward, pass_job_queue=True)
    )

    dp.add_handler(
        CommandHandler("start", actions.on_start_command, pass_user_data=True)
    )
    dp.add_handler(
        CommandHandler(
            "skip", actions.on_skip_command, pass_job_queue=True
        )
    )
    dp.add_handler(CallbackQueryHandler(actions.on_button_click, pass_user_data=True))
    dp.add_handler(
        MessageHandler(
            (Filters.text | Filters.entity),
            actions.on_message,
            pass_user_data=True,
            pass_job_queue=True,
        )
    )

    updater.start_polling()
    updater.idle()

    logger.info("Bot has started successfully")


if __name__ == "__main__":
    main()
