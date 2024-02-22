import html
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from src import constants
from src.handlers.utils import debug


@debug
async def list_jobs_handler(update: Update, context: CallbackContext) -> None:
    args = update.effective_message.text.split()
    chat_id = int(args[1]) if len(args) > 1 else None
    jobs = [job for job in context.job_queue.jobs() if job.data.get("chat_id") == chat_id]
    await update.message.reply_text(
        f"<b>Jobs: {len(jobs)} items</b>\n\n"
        + "\n\n".join(
            [
                f"Job <i>{html.escape(job.name)}</i> ts {html.escape(str(job.next_t)) if job.next_t else 'None'}\nContext: <code>{html.escape(str(job.data))}</code>"
                for job in jobs
            ]
        ),
        parse_mode=ParseMode.HTML,
    )
