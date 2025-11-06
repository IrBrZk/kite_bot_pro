import aiosqlite
import asyncio
from pathlib import Path
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, path: Path = Path("data/kite_bot.db")):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()
        logger.info("Database initialized at %s", self.path)

    async def init_db(self):
        async with aiosqlite.connect(self.path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id INTEGER PRIMARY KEY,
                    first_name TEXT,
                    language TEXT DEFAULT 'en',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL,
                    booking_date TEXT,
                    booking_time TEXT,
                    location TEXT,
                    created_at TEXT NOT NULL
                )
            ''')
            await db.commit()
            logger.info("DB tables ensured")

    async def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,)) as cur:
                row = await cur.fetchone()
                return dict(row) if row else None

    async def create_user(self, telegram_id: int, first_name: str = "") -> Dict[str, Any]:
        now = datetime.utcnow().isoformat()
        async with aiosqlite.connect(self.path) as db:
            await db.execute('''
                INSERT OR IGNORE INTO users (telegram_id, first_name, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (telegram_id, first_name, now, now))
            await db.commit()
        return {"telegram_id": telegram_id, "first_name": first_name, "created_at": now}

    async def update_user(self, telegram_id: int, **kwargs) -> bool:
        if not kwargs:
            return False
        kwargs['updated_at'] = datetime.utcnow().isoformat()
        keys = ", ".join([f"{k}=?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [telegram_id]
        async with aiosqlite.connect(self.path) as db:
            await db.execute(f'UPDATE users SET {keys} WHERE telegram_id = ?', values)
            await db.commit()
        return True

    async def set_user_language(self, telegram_id: int, language: str) -> bool:
        user = await self.get_user(telegram_id)
        if not user:
            await self.create_user(telegram_id)
        return await self.update_user(telegram_id, language=language)
