import logging
from logging import config
import os

import grpc
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
    OTLPLogExporter,
)
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource

dsn = os.environ.get("UPTRACE_DSN")

resource = Resource(
    attributes={"service.name": "wachter-bot", "service.version": "1.1.0"}
)
logger_provider = LoggerProvider(resource=resource)
set_logger_provider(logger_provider)

exporter = OTLPLogExporter(
    endpoint="otlp.uptrace.dev:4317",
    headers=(("uptrace-dsn", dsn),),
    timeout=5,
    compression=grpc.Compression.Gzip,
)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))

log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "wachter_telegram": {
            "class": "telegram_logger.TelegramHandler",
            "token": os.environ["TELEGRAM_TOKEN"],
            "chat_ids": [os.environ["TELEGRAM_ERROR_CHAT_ID"]],
        },
        "wachter_oltp": {
            "class": "opentelemetry.sdk._logs.LoggingHandler",
            "level": logging.INFO,
            "logger_provider": logger_provider,
        }
    },
    "loggers": {
        "wachter_telegram_logger": {
            "level": "INFO",
            "handlers": [
                "wachter_telegram",
                "wachter_oltp",
            ],
        }
    },
}

config.dictConfig(log_config)
tg_logger = logging.getLogger("wachter_telegram_logger")
