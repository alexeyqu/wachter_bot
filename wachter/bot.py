from telegram.ext import Updater, CommandHandler, Filters, MessageHandler, CallbackQueryHandler
import actions
import os


def main():
    updater = Updater(os.environ['TELEGRAM_TOKEN'])
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("help", actions.on_help_command))
    dp.add_error_handler(actions.on_error)

    dp.add_handler(CommandHandler('start', actions.on_start_command, pass_user_data=True))
    dp.add_handler(CallbackQueryHandler(actions.on_button_click, pass_user_data=True))
    dp.add_handler(MessageHandler(Filters.text, actions.on_message, pass_user_data=True))

    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members,
                                  actions.on_new_chat_member, pass_job_queue=True))
    dp.add_handler(MessageHandler(Filters.entity('hashtag'), actions.on_successful_introduce,
                                  pass_job_queue=True, edited_updates=True))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
