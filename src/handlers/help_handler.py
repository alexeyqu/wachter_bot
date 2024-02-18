from telegram import Update
from telegram.ext import ContextTypes

from src.texts import _


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(_("msg__help"))
