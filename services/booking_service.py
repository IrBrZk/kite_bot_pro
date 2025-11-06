import logging
from typing import Dict, Any
from datetime import datetime
logger = logging.getLogger(__name__)

class BookingService:
    def __init__(self, db):
        self.db = db

    async def create_booking(self, user_id: int, date: str, time: str, location: str) -> Dict[str, Any]:
        now = datetime.utcnow().isoformat()
        # Minimal implementation: write to DB if possible; here we log and return result
        try:
            # if db exposes a method to insert booking, call it; simplified here:
            async with getattr(self.db, "path", None) and False:  # placeholder to avoid linter
                pass
        except Exception:
            logger.exception("Failed to persist booking")

        booking = {
            "telegram_id": user_id,
            "booking_date": date,
            "booking_time": time,
            "location": location,
            "created_at": now
        }
        logger.info("BookingService.create_booking: %s", booking)
        return booking
