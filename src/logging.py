import logging
from logging import config
import os

log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "wachter_telegram": {
            "class": "telegram_logger.TelegramHandler",
            "token": os.environ["TELEGRAM_TOKEN"],
            "chat_ids": [os.environ["TELEGRAM_ERROR_CHAT_ID"]],
        }
    },
    "loggers": {
        "wachter_telegram_logger": {
            "level": "INFO",
            "handlers": ["wachter_telegram",]
        }
    }
}

config.dictConfig(log_config)
tg_logger = logging.getLogger("wachter_telegram_logger")
