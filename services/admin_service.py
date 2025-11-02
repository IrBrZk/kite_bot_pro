# services/admin_service.py
import logging
from typing import Dict, List
from config.settings import ADMIN_IDS

logger = logging.getLogger(__name__)

class AdminService:
    def __init__(self, booking_service, gallery_service, database_service, language_manager):
        self.booking_service = booking_service
        self.database_service = database_service
        self.language_manager = language_manager
        self.gallery_service = gallery_service
        self.database_service = database_service    
    
    def is_admin(self, user_id: int) -> bool:
        """Проверить, является ли пользователь админом"""
        return user_id in ADMIN_IDS
    
    def get_statistics(self) -> Dict:
        """Получить статистику бота"""
        total_bookings = len(self.booking_service.bookings)
        confirmed_bookings = len([b for b in self.booking_service.bookings.values() 
                                if b['status'] == 'confirmed'])
        
        return {
            'total_bookings': total_bookings,
            'confirmed_bookings': confirmed_bookings,
            'total_users': len(self.booking_service.user_bookings),
            'gallery_items': sum(len(items) for items in self.gallery_service.media_content.values())
        }
    
    def get_today_bookings(self) -> List[Dict]:
        """Получить бронирования на сегодня"""
        today = datetime.now().strftime("%Y-%m-%d")
        today_bookings = []
        
        for booking in self.booking_service.bookings.values():
            if booking['date'] == today and booking['status'] == 'confirmed':
                today_bookings.append(booking)
        
        return sorted(today_bookings, key=lambda x: x['time'])
    
    def format_admin_stats(self, user_id: int) -> str:
        """Форматировать статистику для админа"""
        stats = self.get_statistics()
        today_bookings = self.get_today_bookings()
        
        if self.language_manager.get_user_language(user_id) == 'ru':
            return f"""
📊 **СТАТИСТИКА БОТА**

👥 Пользователей: {stats['total_users']}
📅 Всего бронирований: {stats['total_bookings']}
✅ Активных: {stats['confirmed_bookings']}
📸 Медиа файлов: {stats['gallery_items']}

📅 **СЕГОДНЯШНИЕ БРОНИРОВАНИЯ:** {len(today_bookings)}
"""
        else:
            return f"""
📊 **BOT STATISTICS**

👥 Users: {stats['total_users']}
📅 Total bookings: {stats['total_bookings']}
✅ Active: {stats['confirmed_bookings']}
📸 Media files: {stats['gallery_items']}

📅 **TODAY'S BOOKINGS:** {len(today_bookings)}
"""