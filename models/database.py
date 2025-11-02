# models/database.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class User(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: str = 'en'
    created_at: datetime
    last_activity: datetime

class Booking(BaseModel):
    id: str
    user_id: int
    user_name: str
    date: str
    time: str
    location: str
    status: str
    created_at: datetime
    updated_at: datetime

class MediaContent(BaseModel):
    id: int
    type: str  # 'photo', 'video'
    category: str  # 'photos', 'videos', 'tricks', 'equipment'
    url: str
    caption: str
    description: Optional[str] = None
    added_at: datetime