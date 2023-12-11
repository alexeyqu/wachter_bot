from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    filters,
    MessageHandler,
    CallbackQueryHandler,
    ChatMemberHandler,
    PicklePersistence,
)
from ptbcontrib.ptb_jobstores.sqlalchemy import PTBSQLAlchemyJobStore
from src.custom_filters import filter_bot_added
from src.logging import tg_logger
from src.model import get_uri
from src import handlers
import os


def main():
    application = (
        ApplicationBuilder()
        .persistence(PicklePersistence(filepath="persistent_storage.pickle"))
        .token(os.environ["TELEGRAM_TOKEN"])
        .build()
    )
    application.job_queue.scheduler.add_jobstore(
        PTBSQLAlchemyJobStore(
            application=application,
            url=os.environ["PERSISTENCE_DATABASE_URL"],
        )
    )

    application.add_handler(CommandHandler("help", handlers.help_handler))
    application.add_handler(CommandHandler("listjobs", handlers.list_jobs_handler))

    # group UX
    application.add_handler(
        ChatMemberHandler(
            handlers.my_chat_member_handler,
            ChatMemberHandler.MY_CHAT_MEMBER,
        )
    )
    application.add_handler(
        MessageHandler(
            filters.Entity("hashtag") & filters.ChatType.GROUPS,
            handlers.on_hashtag_message,
        )
    )
    application.add_handler(
        MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS & filter_bot_added,
            handlers.on_new_chat_members,
        )
    )

    # admin UX
    application.add_handler(CommandHandler("start", handlers.start_handler))
    application.add_handler(CallbackQueryHandler(handlers.button_handler))
    application.add_handler(
        MessageHandler((filters.TEXT | filters.Entity), handlers.message_handler)
    )
    application.add_error_handler(handlers.error_handler)

    tg_logger.info("Bot has started successfully")
    application.run_polling()


if __name__ == "__main__":
    main()
