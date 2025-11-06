"""
Lightweight harness to call async handlers from scaffold without running Telegram.
Run: ./venv/bin/python tests/harness_callbacks.py
"""
import asyncio
import logging
from types import SimpleNamespace
from app.container import create_container
import handlers.callbacks as callbacks
import handlers.booking as booking
import handlers.commands as commands

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("harness")

class MockCallbackQuery:
    def __init__(self, data, user_id=12345):
        self.data = data
        self.from_user = SimpleNamespace(id=user_id, first_name="TestUser")
        self.message = SimpleNamespace(reply_text=self._reply_text)
    async def answer(self):
        logger.info("MockCallbackQuery.answer()")
    async def edit_message_reply_markup(self, reply_markup=None):
        logger.info("MockCallbackQuery.edit_message_reply_markup called")
    async def _reply_text(self, text, **kwargs):
        logger.info("MockCallbackQuery.reply_text: %s", text)

class MockMessage:
    def __init__(self, text):
        self.text = text
        self.from_user = SimpleNamespace(id=111, first_name="TestUser")
    async def reply_text(self, text, **kwargs):
        logger.info("MockMessage.reply_text: %s", text)

class MockUpdate:
    def __init__(self, message=None, callback_query=None, user_id=111):
        self.message = message
        self.callback_query = callback_query
        self.effective_user = SimpleNamespace(id=user_id)
        self.effective_chat = SimpleNamespace(id=9999)

class MockContext:
    def __init__(self, app_container=None):
        self.user_data = {}
        class App:
            pass
        self.application = SimpleNamespace(container=app_container)

async def run_tests():
    container = create_container()
    # initialize DB for tests quickly
    await container.db.init_db()

    # Test calendar callback
    logger.info("Test: calendar callback")
    upd = MockUpdate(callback_query=MockCallbackQuery("calendar_2025_11", user_id=111))
    ctx = MockContext(app_container=container)
    await callbacks.handle_calendar_callback(upd, ctx)

    # Test date selection callback
    logger.info("Test: book_date callback")
    upd = MockUpdate(callback_query=MockCallbackQuery("book_date_2025-11-10", user_id=111))
    await callbacks.handle_calendar_callback(upd, ctx)

    # Test final confirmation handler via message
    logger.info("Test: final confirmation")
    msg = MockMessage("✅ Подтвердить бронирование")
    upd = MockUpdate(message=msg, user_id=111)
    ctx = MockContext(app_container=container)
    ctx.user_data.update({
        "booking_date": "2025-11-10",
        "booking_time": "09:00",
        "booking_location": "dubai"
    })
    await booking.handle_final_confirmation(upd, ctx)

if __name__ == "__main__":
    asyncio.run(run_tests())
