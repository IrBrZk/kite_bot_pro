# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

# ==================== TELEGRAM ====================
TELEGRAM_BOT_TOKEN = os.getenv('KITE_KEY')

# ==================== CONTACTS ====================
CONTACTS = {
    'phone': '+971 564327509',
    'telegram': '@abdula_kite_pro',
    'instagram': '@abdula_kite_dubai',
    'email': 'abdula@kite.ae',
    'support_hours': 'Ежедневно с 7:00 до 18:00'
}

# ==================== LOCATIONS ====================
LOCATIONS = {
    'dubai': {
        'names': {
            'ru': 'Kite Beach Dubai',
            'en': 'Kite Beach Dubai', 
            'ar': 'كايت بيتش دبي'
        },
        'levels': ['beginner', 'intermediate', 'advanced'],
        'description': {
            'ru': 'Мелкая вода, ровный ветер',
            'en': 'Shallow water, steady wind',
            'ar': 'مياه ضحلة، رياح مستقرة'
        },
        'best_time': '10:00-18:00'
    },
    'abudhabi': {
        'names': {
            'ru': 'Kite Beach Abu Dhabi',
            'en': 'Kite Beach Abu Dhabi',
            'ar': 'كايت بيتش أبوظبي'
        },
        'levels': ['beginner', 'intermediate'],
        'description': {
            'ru': 'Широкая пляжная зона',
            'en': 'Wide beach area', 
            'ar': 'منطقة شاطئية واسعة'
        },
        'best_time': 'Утренние часы'
    },
    'jebelali': {
        'names': {
            'ru': 'Jebel Ali Kite Beach',
            'en': 'Jebel Ali Kite Beach',
            'ar': 'جبل علي كايت بيتش'
        },
        'levels': ['advanced'],
        'description': {
            'ru': 'Сильный ровный ветер',
            'en': 'Strong steady wind',
            'ar': 'رياح قوية مستقرة'
        },
        'best_time': 'После 14:00'
    }
}

# ==================== GALLERY & PROMO ====================
GALLERY = {
    'social_links': {
        'instagram': 'https://instagram.com/abdula_kite_dubai',
        'youtube': 'https://youtube.com/c/AbdulaKitePro',
        'tiktok': 'https://tiktok.com/@abdula_kite'
    },
    'promo_content': {
        'photos': {
            'ru': 'Фото с занятий 📷',
            'en': 'Lesson photos 📷',
            'ar': 'صور الدروس 📷'
        },
        'videos': {
            'ru': 'Видео прогресса студентов 🎥',
            'en': 'Student progress videos 🎥', 
            'ar': 'فيديوهات تقدم الطلاب 🎥'
        },
        'tricks': {
            'ru': 'Трюки и техники катания 🏄‍♂️',
            'en': 'Kite tricks and techniques 🏄‍♂️',
            'ar': 'حيل وتقنيات الكايت 🏄‍♂️'
        },
        'equipment': {
            'ru': 'Обзоры оборудования 🔧',
            'en': 'Equipment reviews 🔧',
            'ar': 'مراجعات المعدات 🔧'
        }
    }
}

# ==================== SCHEDULE ====================
SCHEDULE = {
    'time_slots': ['07:00', '08:00', '09:00', '10:00', '11:00', '12:00', 
                   '13:00', '14:00', '15:00', '16:00', '17:00', '18:00'],
    'lesson_duration': 60,
    'working_hours': {'start': '07:00', 'end': '18:00'}
}

# ==================== ADMIN ====================
ADMIN_IDS = [224853932]  # Ваш ID

# ==================== AI CONFIG ====================
AI_CONFIG = {
    'timeout': 30,
    'model': 'gpt-3.5-turbo'
}

# config/settings.py - ДОБАВИТЬ В КОНЕЦ

# ==================== LOT CONFIG ====================
LOT_DURATION = 60  # Длительность одного лота в минутах (1 час)
MIN_LOTS = 1       # Минимальное количество лотов
MAX_LOTS = 8       # Максимальное количество лотов подряд