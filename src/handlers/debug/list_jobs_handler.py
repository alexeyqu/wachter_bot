import html
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from src import constants
from src.handlers.utils import debug


@debug
def list_jobs_handler(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        f"<b>Jobs: {len(context.job_queue.jobs())} items</b>\n\n"
        + "\n\n".join(
            [
                f"Job <i>{html.escape(job.name)}</i> ts {html.escape(str(job.next_t)) if job.next_t else 'None'}\nContext: <code>{html.escape(str(job.context))}</code>"
                for job in context.job_queue.jobs()
            ]
        ),
        parse_mode=ParseMode.HTML,
    )
