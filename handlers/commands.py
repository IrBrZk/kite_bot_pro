import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else None
    logger.info("ENTER start_handler: user_id=%s", user_id)
    # Delegate logic to services via context.application.container if needed
    await update.message.reply_text("Привет! Выберите язык / Choose language")

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Help: send /start to begin")
