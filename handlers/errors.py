import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Unhandled exception in update: %s", getattr(context, "error", None))
    try:
        if update and getattr(update, "message", None):
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте еще раз.")
    except Exception:
        logger.exception("Failed to notify user about error.")
