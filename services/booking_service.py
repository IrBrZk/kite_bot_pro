# services/booking_service.py
# -*- coding: utf-8 -*-
from services.database_service import DatabaseService
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from config.settings import SCHEDULE, LOCATIONS
from config.constants import BookingStatus

logger = logging.getLogger(__name__)

class BookingService:
    def __init__(self, database_service: DatabaseService):
        self.database_service = database_service
        self.bookings: Dict[str, Dict] = {}
        self.user_bookings: Dict[int, List[str]] = {}
    
    def generate_booking_id(self, user_id: int, date: str, time: str, lot: int = 1) -> str:
        """Генерация уникального ID бронирования с учетом лота"""
        return f"{user_id}_{date.replace('-', '')}_{time.replace(':', '')}_{lot}"
    
    def get_available_dates(self) -> List[str]:
        """Получить доступные даты (следующие 7 дней)"""
        today = datetime.now().date()
        return [(today + timedelta(days=i)).strftime("%Y-%m-%d") 
                for i in range(1, 8)]
    
    def get_available_times(self, date: str, location: str) -> List[str]:
        """Получить доступное время для даты и локации"""
        return SCHEDULE['time_slots']
    
    def create_booking(self, user_id: int, date: str, time: str, 
                      location: str, user_name: str,
                      user_phone: str = None, user_email: str = None,
                      lots: int = 1) -> Optional[Dict]:
        """Создать бронирование для указанного количества часов"""
        try:
            booking_id = self.generate_booking_id(user_id, date, time, lots)
            
            booking = {
                'id': booking_id,
                'user_id': user_id,
                'user_name': user_name,
                'user_phone': user_phone,
                'user_email': user_email,
                'date': date,
                'time': time,
                'location': location,
                'lots': lots,  # Количество часов
                'duration_minutes': lots * 60,  # Продолжительность в минутах
                'status': BookingStatus.BOOKED,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self.bookings[booking_id] = booking
            
            # Добавляем в список бронирований пользователя
            if user_id not in self.user_bookings:
                self.user_bookings[user_id] = []
            self.user_bookings[user_id].append(booking_id)
            
            logger.info(f"✅ Booking created: {booking_id} for {lots} hours")
            
            # TODO: Отправить уведомление админу
            logger.info(f"📢 Admin notification: New booking from user {user_id} for {lots} hours")
            
            return booking
            
        except Exception as e:
            logger.error(f"❌ Error creating booking: {e}")
            return None
    
    def get_user_bookings(self, user_id: int) -> List[Dict]:
        """Получить все бронирования пользователя"""
        if user_id not in self.user_bookings:
            return []
        
        user_booking_ids = self.user_bookings[user_id]
        return [self.bookings.get(booking_id) for booking_id in user_booking_ids 
                if booking_id in self.bookings]
    
    def cancel_booking(self, booking_id: str) -> bool:
        """Отменить бронирование"""
        if booking_id in self.bookings:
            self.bookings[booking_id]['status'] = BookingStatus.CANCELLED
            self.bookings[booking_id]['updated_at'] = datetime.now().isoformat()
            logger.info(f"✅ Booking cancelled: {booking_id}")
            return True
        return False

# Глобальный экземпляр
booking_service = BookingService(DatabaseService())
