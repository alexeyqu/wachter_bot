from telegram import InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from src import constants
from src.handlers.utils import debug


@debug
def list_jobs_handler(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(f"Jobs: {len(context.job_queue.jobs())} items\n\n" + "\n".join([
        f"Job {job.name}\n Context: {job.context}"
        for job in context.job_queue.jobs()
    ]))
