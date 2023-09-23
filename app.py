from telegram.ext import (
    Updater,
    CommandHandler,
    Filters,
    MessageHandler,
    CallbackQueryHandler,
)
from src.custom_filters import filter_bot_added
from src.logging import tg_logger
from src import handlers
import os


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
    tg_logger.info("Bot has started successfully")
    updater.idle()


if __name__ == "__main__":
    main()