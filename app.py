from telegram.ext import (
    Updater,
    CommandHandler,
    Filters,
    MessageHandler,
    CallbackQueryHandler,
)
from src.custom_filters import filter_bot_added
from src import handlers
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

    dp.add_handler(CommandHandler("help", handlers.help_handler))
    dp.add_error_handler(handlers.error_handler)

    # group UX
    dp.add_handler(
        MessageHandler(
            Filters.entity("hashtag"),
            handlers.on_hashtag_message,
            pass_job_queue=True,
            pass_user_data=True,
        )
    )
    dp.add_handler(
        MessageHandler(
            (Filters.text | Filters.entity),
            handlers.message_handler,
            pass_user_data=True,
            pass_job_queue=True,
        )
    )

    # admin UX
    dp.add_handler(
        CommandHandler("start", handlers.start_handler, pass_user_data=True)
    )
    dp.add_handler(
        MessageHandler(
            Filters.status_update.new_chat_members & filter_bot_added,
            handlers.on_new_chat_member,
            pass_job_queue=True,
        )
    )
    dp.add_handler(CallbackQueryHandler(handlers.button_handler, pass_user_data=True))

    updater.start_polling()
    logger.info("Bot has started successfully")
    updater.idle()


if __name__ == "__main__":
    main()