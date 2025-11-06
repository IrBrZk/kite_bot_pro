import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def start_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("ENTER start_booking for user %s", update.effective_user.id)
    await update.message.reply_text("Let's start booking. Choose a date.")

async def handle_final_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("ENTER handle_final_confirmation for user %s", update.effective_user.id)
    # expected: context.user_data contains booking info
    bd = context.user_data.get("booking_date")
    bt = context.user_data.get("booking_time")
    if not bd or not bt:
        await update.message.reply_text("No booking data found.")
        return
    # Delegate to booking service
    container = getattr(context.application, "container", None)
    if container:
        booking = await container.booking_service.create_booking(
            user_id=update.effective_user.id,
            date=bd, time=bt, location=context.user_data.get("booking_location", "unknown")
        )
        await update.message.reply_text(f"Booking created: {booking}")
    else:
        await update.message.reply_text("Booking service unavailable in context.")
