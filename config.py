# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
KITE_KEY = os.getenv('KITE_KEY')

# AI Configuration
AI_KEY = os.getenv('AI_KEY')
AI_MODEL = "gpt-3.5-turbo"
AI_TIMEOUT = 10
AI_TEMPERATURE = 0.1

# Server Configuration
SERVER_TIMEOUT = 30

# Supported Languages
SUPPORTED_LANGUAGES = {
    'en': 'English 🇺🇸',
    'ru': 'Russian 🇷🇺', 
    'ar': 'Arabic 🇦🇪',
    'es': 'Spanish 🇪🇸'
}

# Texts
TEXTS = {
    'spots_info': "🏄‍♂️ **ЛУЧШИЕ СПОТЫ ДЛЯ КАЙТСЕРФИНГА В ОАЭ:**\n\n1. Kite Beach Dubai 🌊\n2. Kite Beach Abu Dhabi 🏖️\n3. Jebel Ali Kite Beach 💨\n4. Al Hamra Kite Beach 🏝️\n5. Sunset Beach Umm Al Quwain 🌅",
    'contacts_info': "📞 **КОНТАКТЫ АБДУЛЫ:**\n\n**Телефон:** +971 564327509\n**Telegram:** @abdula_kite_pro\n**Instagram:** @abdula_kite_dubai"
}