import logging
from typing import Optional
logger = logging.getLogger(__name__)

class LanguageManager:
    def __init__(self, db=None):
        self.db = db
        self._cache = {}

    async def get_user_language(self, telegram_id: int) -> str:
        if telegram_id in self._cache:
            return self._cache[telegram_id]
        if self.db:
            user = await self.db.get_user(telegram_id)
            lang = user.get("language") if user else "en"
            self._cache[telegram_id] = lang
            return lang
        return "en"

    async def set_user_language(self, telegram_id: int, language: str):
        self._cache[telegram_id] = language
        if self.db:
            await self.db.set_user_language(telegram_id, language)
