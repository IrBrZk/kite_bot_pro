import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def handle_calendar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        logger.warning("handle_calendar_callback called without callback_query")
        return
    await query.answer()
    logger.info("Calendar callback data: %s", query.data)
    # Minimal behavior: echo back the data as confirmation in mocks
    await query.edit_message_reply_markup(reply_markup=None)
