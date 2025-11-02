# services/database_service.py
import logging
import json
import os
from datetime import datetime
from typing import Optional, Dict, List
from models.user_model import User

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.users: Dict[int, User] = {}
        self.data_file = 'data/users.json'
        self.load_users()
    
    def load_users(self):
        """Загрузить пользователей из JSON файла"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for user_data in data:
                        # Конвертируем строки дат обратно в datetime
                        user_data['registration_date'] = datetime.fromisoformat(user_data['registration_date'])
                        user_data['last_activity'] = datetime.fromisoformat(user_data['last_activity'])
                        if user_data.get('last_contact_date'):
                            user_data['last_contact_date'] = datetime.fromisoformat(user_data['last_contact_date'])
                        
                        user = User(**user_data)
                        self.users[user.telegram_id] = user
                logger.info(f"✅ Loaded {len(self.users)} users from database")
            else:
                logger.info("No existing user database found, starting fresh")
        except Exception as e:
            logger.error(f"❌ Error loading users: {e}")
    
    def save_users(self):
        """Сохранить пользователей в JSON файл"""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            
            users_data = []
            for user in self.users.values():
                user_dict = user.dict()
                # Конвертируем datetime в строки для JSON
                user_dict['registration_date'] = user.registration_date.isoformat()
                user_dict['last_activity'] = user.last_activity.isoformat()
                if user.last_contact_date:
                    user_dict['last_contact_date'] = user.last_contact_date.isoformat()
                users_data.append(user_dict)
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(users_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 Saved {len(users_data)} users to database")
        except Exception as e:
            logger.error(f"❌ Error saving users: {e}")
    
    def get_user(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        return self.users.get(telegram_id)
    
    def create_user(self, telegram_user, language: str = 'en') -> User:
        """Создать нового пользователя"""
        now = datetime.now()
        user = User(
            user_id=len(self.users) + 1,
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            language=language,
            registration_date=now,
            last_activity=now,
            messages_count=1
        )
        
        self.users[user.telegram_id] = user
        self.save_users()
        logger.info(f"✅ New user created: {user.telegram_id} - {user.first_name}")
        return user
    
    def update_user_activity(self, telegram_id: int, command: str = None):
        """Обновить активность пользователя"""
        user = self.get_user(telegram_id)
        if user:
            user.last_activity = datetime.now()
            user.messages_count += 1
            if command:
                user.last_command = command
            self.save_users()
    
    def set_user_language(self, telegram_id: int, language: str):
        """Установить язык пользователя"""
        user = self.get_user(telegram_id)
        if user:
            user.language = language
            user.language_selected = True
            self.save_users()
            logger.info(f"Language set to {language} for user {telegram_id}")
    
    def update_user_level(self, telegram_id: int, level: str, score: int = None):
        """Обновить уровень пользователя"""
        user = self.get_user(telegram_id)
        if user:
            user.skill_level = level
            user.level_test_completed = True
            if score:
                user.test_score = score
            self.save_users()
    
    def increment_bookings(self, telegram_id: int):
        """Увеличить счетчик бронирований"""
        user = self.get_user(telegram_id)
        if user:
            user.bookings_count += 1
            self.save_users()
    
    def get_user_stats(self, telegram_id: int) -> Dict:
        """Получить статистику пользователя"""
        user = self.get_user(telegram_id)
        if not user:
            return {}
        
        return {
            'user_id': user.user_id,
            'name': f"{user.first_name} {user.last_name or ''}",
            'language': user.language,
            'registration_date': user.registration_date.strftime("%Y-%m-%d"),
            'messages_count': user.messages_count,
            'bookings_count': user.bookings_count,
            'completed_lessons': user.completed_lessons,
            'skill_level': user.skill_level,
            'preferred_location': user.preferred_location
        }
    
    def get_all_users(self) -> List[User]:
        """Получить всех пользователей"""
        return list(self.users.values())
    
    def get_active_users_count(self) -> int:
        """Получить количество активных пользователей"""
        return len([u for u in self.users.values() if u.is_active])
    
    def update_user_preferences(self, telegram_id: int, location: str = None, time_slot: str = None):
        """Обновить предпочтения пользователя"""
        user = self.get_user(telegram_id)
        if user:
            if location:
                user.preferred_location = location
            if time_slot:
                user.preferred_time_slot = time_slot
            self.save_users()