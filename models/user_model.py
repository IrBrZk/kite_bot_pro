# models/user_model.py
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel

class User(BaseModel):
    # Основные данные
    telegram_id: int
    username: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None
    phone: Optional[str] = None
    
    # Язык и локализация
    language: str = 'en'
    language_selected: bool = False
    
    # Статистика и активность
    registration_date: datetime
    last_activity: datetime
    messages_count: int = 0
    bookings_count: int = 0
    completed_lessons: int = 0
    
    # Уровень и прогресс
    skill_level: str = 'unknown'
    level_test_completed: bool = False
    test_score: Optional[int] = None
    
    # Предпочтения
    preferred_location: Optional[str] = None
    preferred_time_slot: Optional[str] = None
    equipment_rental: bool = False
    
    # Маркетинг
    source: Optional[str] = None
    referrals: int = 0
    subscribed_to_news: bool = True
    
    # Технические поля
    is_active: bool = True
    is_blocked: bool = False
    last_command: Optional[str] = None
    user_data: Dict[str, Any] = {}
    
    # Контакты
    contact_permission: bool = False
    last_contact_date: Optional[datetime] = None
    
    def to_db_row(self):
        """Конвертировать в кортеж для SQLite"""
        return (
            self.telegram_id, self.username, self.first_name, self.last_name,
            self.phone, self.language, self.language_selected,
            self.registration_date.isoformat(), self.last_activity.isoformat(),
            self.messages_count, self.bookings_count, self.completed_lessons,
            self.skill_level, self.level_test_completed, self.test_score,
            self.preferred_location, self.preferred_time_slot, self.equipment_rental,
            self.source, self.referrals, self.subscribed_to_news,
            self.is_active, self.is_blocked, self.last_command,
            self.contact_permission, 
            self.last_contact_date.isoformat() if self.last_contact_date else None
        )
    
    @classmethod
    def from_db_row(cls, row):
        """Создать User из строки SQLite"""
        return cls(
            telegram_id=row[0], username=row[1], first_name=row[2], last_name=row[3],
            phone=row[4], language=row[5], language_selected=bool(row[6]),
            registration_date=datetime.fromisoformat(row[7]),
            last_activity=datetime.fromisoformat(row[8]),
            messages_count=row[9], bookings_count=row[10], completed_lessons=row[11],
            skill_level=row[12], level_test_completed=bool(row[13]), test_score=row[14],
            preferred_location=row[15], preferred_time_slot=row[16], equipment_rental=bool(row[17]),
            source=row[18], referrals=row[19], subscribed_to_news=bool(row[20]),
            is_active=bool(row[21]), is_blocked=bool(row[22]), last_command=row[23],
            contact_permission=bool(row[24]),
            last_contact_date=datetime.fromisoformat(row[25]) if row[25] else None
        )
