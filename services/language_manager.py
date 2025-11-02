import logging
from typing import Dict

logger = logging.getLogger(__name__)

class LanguageManager:
    def __init__(self):
        self.user_languages: Dict[int, str] = {}
        self.texts = {
            'ru': {
                'welcome': 'Привет, {first_name}! 🎉 Добро пожаловать в кайт-школу Абдулы!',
                'menu_booking': '📅 Бронирование',
                'menu_my_bookings': '📋 Мои брони',
                'menu_level_test': '🎯 Тест уровня', 
                'menu_safety': '🛟 Безопасность',
                'menu_locations': '📍 Локации',
                'menu_contacts': '📞 Контакты',
                'menu_language': '🌐 Язык',
                'menu_gallery': '📸 Галерея',
                'menu_home': '🏠 Домой',
                'booking_choose_date': '📅 Выберите дату для занятия',
                'booking_choose_time': '🕐 Выберите время',
                'booking_choose_location': '📍 Выберите локацию',
                'booking_enter_contacts': '📞 Введите контактные данные',
                'booking_confirm': '✅ Подтвердить бронирование',
                'booking_cancel': '❌ Отменить'
            },
            'en': {
                'welcome': 'Hello, {first_name}! 🎉 Welcome to Abdula Kite School!',
                'menu_booking': '📅 Booking',
                'menu_my_bookings': '📋 My Bookings',
                'menu_level_test': '🎯 Level Test',
                'menu_safety': '🛟 Safety', 
                'menu_locations': '📍 Locations',
                'menu_contacts': '📞 Contacts',
                'menu_language': '🌐 Language',
                'menu_gallery': '📸 Gallery',
                'menu_home': '🏠 Home',
                'booking_choose_date': '📅 Choose date for lesson',
                'booking_choose_time': '🕐 Choose time',
                'booking_choose_location': '📍 Choose location',
                'booking_enter_contacts': '📞 Enter contact details',
                'booking_confirm': '✅ Confirm booking',
                'booking_cancel': '❌ Cancel'
            },
            'ar': {
                'welcome': 'مرحباً, {first_name}! 🎉 أهلاً بك في مدرسة عبدلة للطائرات الورقية!',
                'menu_booking': '📅 الحجز',
                'menu_my_bookings': '📋 حجوزاتي',
                'menu_level_test': '🎯 اختبار المستوى',
                'menu_safety': '🛟 السلامة',
                'menu_locations': '📍 المواقع',
                'menu_contacts': '📞 جهات الاتصال', 
                'menu_language': '🌐 اللغة',
                'menu_gallery': '📸 المعرض',
                'menu_home': '🏠 الرئيسية',
                'booking_choose_date': '📅 اختر تاريخ الدرس',
                'booking_choose_time': '🕐 اختر الوقت',
                'booking_choose_location': '📍 اختر الموقع',
                'booking_enter_contacts': '📞 أدخل بيانات الاتصال',
                'booking_confirm': '✅ تأكيد الحجز',
                'booking_cancel': '❌ إلغاء'
            }
        }
    
    def get_user_language(self, user_id: int) -> str:
        """Получить язык пользователя"""
        return self.user_languages.get(user_id, 'en')
    
    def set_user_language(self, user_id: int, language: str):
        """Установить язык пользователя"""
        if language in ['ru', 'en', 'ar']:
            self.user_languages[user_id] = language
            logger.info(f"Language set to {language} for user {user_id}")
    
    def get_text(self, user_id: int, key: str, **kwargs) -> str:
        """Получить текст на языке пользователя с форматированием"""
        lang = self.get_user_language(user_id)
        text_template = self.texts.get(lang, {}).get(key, self.texts['en'].get(key, key))
        return text_template.format(**kwargs) if kwargs else text_template
    
    def get_all_menu_texts(self, user_id: int) -> Dict[str, str]:
        """Получить все тексты меню для пользователя"""
        lang = self.get_user_language(user_id)
        return self.texts.get(lang, self.texts['en'])

# Глобальный экземпляр
language_manager = LanguageManager()
