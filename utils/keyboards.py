# utils/keyboards.py
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict
from config.constants import SUPPORTED_LANGUAGES
from config.settings import LOCATIONS
from services.language_manager import LanguageManager
from services.booking_service import BookingService

class KeyboardManager:
    def __init__(self, language_manager: LanguageManager, booking_service: BookingService):
        self.language_manager = language_manager
        self.booking_service = booking_service
    
    def get_main_menu(self, user_id: int) -> ReplyKeyboardMarkup:
        """Главное меню"""
        texts = self.language_manager.get_all_menu_texts(user_id)
        
        keyboard = [
            [texts['booking'], texts['level_test']],
            [texts['locations'], texts['safety']],
            [texts['contacts'], texts['gallery']],
            [texts['language']]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    def get_language_keyboard(self) -> ReplyKeyboardMarkup:
        """Клавиатура выбора языка"""
        languages = list(SUPPORTED_LANGUAGES.values())
        keyboard = [
            [languages[0], languages[1]],
            [languages[2]]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    def get_back_keyboard(self, user_id: int) -> ReplyKeyboardMarkup:
        """Клавиатура с кнопкой Назад"""
        back_text = self.language_manager.get_text(user_id, 'menu.back')
        keyboard = [[back_text]]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    def get_dates_keyboard(self) -> ReplyKeyboardMarkup:
        """Клавиатура с датами (следующие 7 дней)"""
        dates = self.booking_service.get_available_dates()
        
        keyboard = []
        row = []
        for i, date in enumerate(dates):
            row.append(date)
            if len(row) == 2 or i == len(dates) - 1:
                keyboard.append(row)
                row = []
        
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    def get_times_keyboard(self) -> ReplyKeyboardMarkup:
        """Клавиатура со временем"""
        from config.settings import SCHEDULE
        times = SCHEDULE['time_slots']
        
        keyboard = []
        row = []
        for i, time in enumerate(times):
            row.append(time)
            if len(row) == 3 or i == len(times) - 1:
                keyboard.append(row)
                row = []
        
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    def get_locations_keyboard(self, user_id: int) -> ReplyKeyboardMarkup:
        """Клавиатура с локациями"""
        user_lang = self.language_manager.get_user_language(user_id)
        
        keyboard = []
        for loc_id, loc_data in LOCATIONS.items():
            location_name = loc_data['names'].get(user_lang, loc_data['names']['en'])
            keyboard.append([location_name])
        
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    def get_gallery_categories_keyboard(self, user_id: int) -> ReplyKeyboardMarkup:
        """Клавиатура категорий галереи"""
        from services.gallery_service import GalleryService
        gallery_service = GalleryService(self.language_manager)
        categories = gallery_service.get_gallery_categories(user_id)
        
        keyboard = []
        row = []
        for i, category in enumerate(categories):
            row.append(category['name'])
            if len(row) == 2 or i == len(categories) - 1:
                keyboard.append(row)
                row = []
        
        back_text = self.language_manager.get_text(user_id, 'menu.back')
        keyboard.append([back_text])
        
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    def get_admin_keyboard(self, user_id: int) -> ReplyKeyboardMarkup:
        """Админ клавиатура"""
        texts = self.language_manager.get_all_menu_texts(user_id)
        
        keyboard = [
            ["📊 Статистика", "📅 Сегодняшние записи"],
            ["📸 Добавить медиа", "🔄 Обновить контент"],
            [texts['home']]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    def get_confirmation_keyboard(self, user_id: int) -> ReplyKeyboardMarkup:
        """Клавиатура подтверждения"""
        user_lang = self.language_manager.get_user_language(user_id)
        
        if user_lang == 'ru':
            confirm_text = "✅ Подтвердить"
            cancel_text = "❌ Отменить"
        elif user_lang == 'ar':
            confirm_text = "✅ تأكيد"
            cancel_text = "❌ إلغاء"
        else:
            confirm_text = "✅ Confirm"
            cancel_text = "❌ Cancel"
        
        keyboard = [
            [confirm_text, cancel_text]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
