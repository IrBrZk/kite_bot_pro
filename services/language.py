# services/language.py
import logging
import json
import os
from config import SUPPORTED_LANGUAGES
from database import Database

logger = logging.getLogger(__name__)

class LanguageManager:
    def __init__(self):
        self.db = Database()
        self.translations = self._load_translations()
    
    def _load_translations(self):
        """Загрузка переводов из JSON файлов"""
        translations = {}
        for lang in SUPPORTED_LANGUAGES:
            file_path = f"locales/{lang}.json"
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    translations[lang] = json.load(f)
            except FileNotFoundError:
                logger.warning(f"Translation file {file_path} not found")
                translations[lang] = {}
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in {file_path}")
                translations[lang] = {}
        
        return translations
    
    def get_user_language(self, user_id: int) -> str:
        """Получить язык пользователя"""
        user_data = self.db.get_user(user_id)
        if user_data and user_data[1]:  # language field
            return user_data[1]
        return 'en'
    
    def set_user_language(self, user_id: int, language: str):
        """Установить язык пользователя"""
        if language not in SUPPORTED_LANGUAGES:
            language = 'en'
        self.db.update_user_language(user_id, language)
        logger.info(f"Language set to {language} for user {user_id}")
    
    def get_language_keyboard(self):
        """Клавиатура для выбора языка"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        language_names = {
            'en': 'English 🇺🇸',
            'ru': 'Русский 🇷🇺',
            'ar': 'العربية 🇦🇪',
            'es': 'Español 🇪🇸',
            'fr': 'Français 🇫🇷', 
            'de': 'Deutsch 🇩🇪'
        }
        
        buttons = []
        for lang_code in SUPPORTED_LANGUAGES:
            button = InlineKeyboardButton(
                language_names[lang_code],
                callback_data=f"lang_{lang_code}"
            )
            buttons.append([button])
            
        return InlineKeyboardMarkup(buttons)
    
    def get_text(self, user_id: int, text_key: str, **kwargs) -> str:
        """Получить текст на языке пользователя"""
        language = self.get_user_language(user_id)
        
        # Получаем перевод
        text = self.translations.get(language, {}).get(text_key)
        
        # Если перевод не найден, используем английский как fallback
        if text is None:
            text = self.translations.get('en', {}).get(text_key, text_key)
        
        # Форматирование если есть kwargs
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, IndexError):
                logger.warning(f"Format error for text_key {text_key}")
        
        return text
    
    def get_main_menu(self, user_id: int):
        """Получить главное меню для пользователя"""
        from utils.helpers import get_main_menu
        return get_main_menu(self, user_id)
