from telegram.ext import (
    CommandHandler,
    Filters,
    MessageHandler,
    PicklePersistence,
    CallbackQueryHandler,
    ChatMemberHandler,
)
import sentry_sdk
from src.custom_filters import filter_bot_added
from src.logging import tg_logger
from src import handlers
from src.job_persistence_updater import JobPersistenceUpdater
import os

if "SENTRY_DSN" in os.environ:
    sentry_sdk.init(
        dsn=os.environ["SENTRY_DSN"],
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )

def main():
    updater = JobPersistenceUpdater(
        os.environ["TELEGRAM_TOKEN"],
        persistence=PicklePersistence(filename="persistent_storage.pickle", store_callback_data=True),
    )
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("help", handlers.help_handler))
    dp.add_handler(CommandHandler("listjobs", handlers.list_jobs_handler))

    # group UX
    dp.add_handler(
        ChatMemberHandler(
            handlers.my_chat_member_handler,
            ChatMemberHandler.MY_CHAT_MEMBER,
        )
    )
    dp.add_handler(
        MessageHandler(
            Filters.entity("hashtag") & Filters.chat_type.groups,
            handlers.on_hashtag_message,
            pass_job_queue=True,
            pass_user_data=True,
        )
    )
    dp.add_handler(
        MessageHandler(
            Filters.status_update.new_chat_members & filter_bot_added,
            handlers.on_new_chat_members,
            pass_job_queue=True,
        )
    )

    # admin UX
    dp.add_handler(CommandHandler("start", handlers.start_handler, pass_user_data=True))
    dp.add_handler(CallbackQueryHandler(handlers.button_handler, pass_user_data=True))
    dp.add_handler(
        MessageHandler(
            (Filters.text | Filters.entity),
            handlers.message_handler,
            pass_user_data=True,
            pass_job_queue=True,
        )
    )
    dp.add_error_handler(handlers.error_handler)

    updater.start_polling()
    tg_logger.info("Bot has started successfully")
    updater.idle()


if __name__ == "__main__":
    main()
