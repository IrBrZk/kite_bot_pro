# services/language_manager.py
import logging

logger = logging.getLogger(__name__)

class LanguageManager:
    def __init__(self):
        self.user_languages = {}
    
    async def detect_language_from_text(self, user_id, text):
        """Определить язык текста с помощью AI"""
        try:
            from services.ai_assistant import AIAssistant
            ai_assistant = AIAssistant()
            detected_lang = await ai_assistant.detect_language(text)
            self.set_user_language(user_id, detected_lang)
            return detected_lang
        except Exception as e:
            logger.error(f"Language detection failed for user {user_id}: {e}")
            self.set_user_language(user_id, 'en')
            return 'en'
    
    def set_user_language(self, user_id, language_code):
        """Установить язык пользователя"""
        self.user_languages[user_id] = language_code
        logger.info(f"Language set to {language_code} for user {user_id}")
    
    def get_user_language(self, user_id):
        """Получить язык пользователя"""
        return self.user_languages.get(user_id, 'en')
    
    def get_text(self, user_id, text_key):
        """Получить текст на языке пользователя"""
        user_lang = self.get_user_language(user_id)
        
        texts = {
            'en': {
                'welcome_detect': "Hello! Detecting your language...",
                'timeout_english': "⏰ Timeout expired. English language set.",
                'manual_language': "🌐 Choose language:",
                'ai_busy': "🤖 AI temporarily unavailable. Using English.",
                'language_changed': "Language changed to {}",
                'menu_booking': "📅 Book Lesson",
                'menu_level_test': "🎯 Level Test", 
                'menu_locations': "📍 Locations",
                'menu_safety': "🛟 Safety",
                'menu_contacts': "📞 Contacts",
                'menu_gallery': "📸 Gallery",
                'menu_language': "🌐 Change Language",
                'level_test': "🎯 **KITE LEVEL TEST**\n\nAnswer 5 questions with numbers 1-3:",
                'safety_guide': "🛟 **SAFETY GUIDE**\n\nBasic safety rules...",
                'gallery_message': "📸 **GALLERY**\n\nPhotos and videos available...",
                'use_menu_buttons': "Please use the menu buttons below:",
                'start_button': "🚀 START",
                'home_button': "🏠 Main Menu",
                'back_button': "↩️ Back",
                'choose_date': "📅 Choose date for lesson:",
                'enter_name': "📝 Enter your name:",
                'choose_location': "🌊 Choose location:",
                'booking_confirmed': "✅ Booking confirmed!",
                'error_insufficient_data': "❌ Error: insufficient data",
                'error_saving': "❌ Error saving"
            },
            'ru': {
                'welcome_detect': "Привет! Определяю ваш язык...",
                'timeout_english': "⏰ Время ожидания истекло. Установлен английский язык.",
                'manual_language': "🌐 Выберите язык:",
                'ai_busy': "🤖 AI временно недоступен. Используем английский.",
                'language_changed': "Язык изменен на {}",
                'menu_booking': "📅 Запись на урок",
                'menu_level_test': "🎯 Тест уровня",
                'menu_locations': "📍 Локации", 
                'menu_safety': "🛟 Безопасность",
                'menu_contacts': "📞 Контакты",
                'menu_gallery': "📸 Галерея",
                'menu_language': "🌐 Сменить язык",
                'level_test': "🎯 **ТЕСТ УРОВНЯ КАТАНИЯ**\n\nОтветьте на 5 вопросов цифрой от 1 до 3:",
                'safety_guide': "🛟 **ТЕХНИКА БЕЗОПАСНОСТИ**\n\nОсновные правила безопасности...",
                'gallery_message': "📸 **ГАЛЕРЕЯ**\n\nФото и видео доступны...",
                'use_menu_buttons': "Пожалуйста, используйте кнопки меню ниже:",
                'start_button': "🚀 START",
                'home_button': "🏠 Главное меню",
                'back_button': "↩️ Назад",
                'choose_date': "📅 Выберите дату для урока:",
                'enter_name': "📝 Как вас зовут?",
                'choose_location': "🌊 Выберите локацию:",
                'booking_confirmed': "✅ Запись подтверждена!",
                'error_insufficient_data': "❌ Ошибка: недостаточно данных",
                'error_saving': "❌ Ошибка при сохранении"
            },
            'ar': {
                'welcome_detect': "مرحباً! أكتشف لغتك...",
                'timeout_english': "⏰ انتهى الوقت. تم تعيين اللغة الإنجليزية.",
                'manual_language': "🌐 اختر اللغة:",
                'ai_busy': "🤖 الذكاء الاصطناعي غير متاح حالياً. نستخدم الإنجليزية.",
                'language_changed': "تم تغيير اللغة إلى {}",
                'menu_booking': "📅 حجز درس",
                'menu_level_test': "🎯 اختبار المستوى",
                'menu_locations': "📍 المواقع",
                'menu_safety': "🛟 السلامة", 
                'menu_contacts': "📞 جهات الاتصال",
                'menu_gallery': "📸 معرض الصور",
                'menu_language': "🌐 تغيير اللغة",
                'level_test': "🎯 **اختبار مستوى الكايت**\n\nأجب على 5 أسئلة بالأرقام 1-3:",
                'safety_guide': "🛟 **دليل السلامة**\n\nقواعد السلامة الأساسية...",
                'gallery_message': "📸 **المعرض**\n\nالصور والفيديوهات متاحة...",
                'use_menu_buttons': "يرجى استخدام أزرار القائمة أدناه:",
                'start_button': "🚀 ابدأ",
                'home_button': "🏠 الرئيسية",
                'back_button': "↩️ رجوع",
                'choose_date': "📅 اختر تاريخ الدرس:",
                'enter_name': "📝 ما هو اسمك؟",
                'choose_location': "🌊 اختر الموقع:",
                'booking_confirmed': "✅ تم تأكيد الحجز!",
                'error_insufficient_data': "❌ خطأ: بيانات غير كافية",
                'error_saving': "❌ خطأ في الحفظ"
            }
        }
        
        lang_texts = texts.get(user_lang, texts['en'])
        return lang_texts.get(text_key, text_key)
    
    def get_personalized_welcome(self, user_id):
        """Получить персонализированное приветствие"""
        user_lang = self.get_user_language(user_id)
        
        welcomes = {
            'en': "Hello friend!!! I am Abdula's bot manager, a super professional coach, champion, and experienced master with many years of experience! 🏄‍♂️",
            'ru': "Привет, друг! Я бот-менеджер Абдулы, суперпрофессионального тренера, чемпиона и опытного мастера с многолетним опытом! 🏄‍♂️",
            'ar': "مرحباً صديقي! أنا بوت عبدلة المدير، مدرب محترف جداً، بطل، ومدرب خبير بخبرة سنوات عديدة! 🏄‍♂️"
        }
        
        return welcomes.get(user_lang, welcomes['en'])
    
    def get_language_keyboard(self):
        """Получить клавиатуру выбора языка"""
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = [
            [
                InlineKeyboardButton("English 🇺🇸", callback_data="lang_en"),
                InlineKeyboardButton("Русский 🇷🇺", callback_data="lang_ru")
            ],
            [
                InlineKeyboardButton("العربية 🇦🇪", callback_data="lang_ar"),
                InlineKeyboardButton("Español 🇪🇸", callback_data="lang_es")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_user_name(self, user_id):
        """Получить имя пользователя"""
        try:
            from database import Database
            db = Database()
            user_data = db.get_user(user_id)
            return user_data[1] if user_data and user_data[1] else None
        except Exception as e:
            logger.error(f"Error getting user name {user_id}: {e}")
            return None