from services.database import Database
from services.booking_service import BookingService
from services.language_manager import LanguageManager
import os
from pathlib import Path

class Config:
    TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    DB_PATH = os.environ.get("KITE_DB", "data/kite_bot.db")

class Container:
    def __init__(self, config):
        self.config = config
        self.db = Database(Path(config.DB_PATH))
        self.language_manager = LanguageManager(self.db)
        self.booking_service = BookingService(self.db)

def create_container():
    return Container(Config)
