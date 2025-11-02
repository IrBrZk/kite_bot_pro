# services/content_manager.py
import logging
from config.settings import CONTACTS, LOCATIONS, GALLERY
from services.language_manager import LanguageManager

logger = logging.getLogger(__name__)

class ContentManager:
    def __init__(self, language_manager: LanguageManager):
        self.language_manager = language_manager
    
    def get_contacts_text(self, user_id: int) -> str:
        """Получить текст контактов"""
        user_lang = self.language_manager.get_user_language(user_id)
        
        if user_lang == 'ru':
            return f"""
📞 **КОНТАКТЫ АБДУЛЫ:**

**Телефон:** {CONTACTS['phone']}
**Telegram:** {CONTACTS['telegram']}
**Instagram:** {CONTACTS['instagram']}

📍 **Где нас найти:**
Основной спот: Kite Beach Dubai
Резервный спот: Kite Beach Abu Dhabi

🕒 **Часы работы:**
{CONTACTS['support_hours']}
"""
        elif user_lang == 'ar':
            return f"""
📞 **جهات اتصال عبدلة:**

**الهاتف:** {CONTACTS['phone']}
**Telegram:** {CONTACTS['telegram']}
**Instagram:** {CONTACTS['instagram']}

📍 **أين تجدنا:**
الموقع الرئيسي: كايت بيتش دبي
الموقع الاحتياطي: كايت بيتش أبوظبي

🕒 **ساعات العمل:**
{CONTACTS['support_hours']}
"""
        else:
            return f"""
📞 **ABDULA'S CONTACTS:**

**Phone:** {CONTACTS['phone']}
**Telegram:** {CONTACTS['telegram']}
**Instagram:** {CONTACTS['instagram']}

📍 **Where to find us:**
Main spot: Kite Beach Dubai
Backup spot: Kite Beach Abu Dhabi

🕒 **Working hours:**
{CONTACTS['support_hours']}
"""
    
    def get_gallery_text(self, user_id: int) -> str:
        """Получить текст галереи"""
        user_lang = self.language_manager.get_user_language(user_id)
        
        if user_lang == 'ru':
            return f"""
📸 **ГАЛЕРЕЯ И ВИДЕО**

Посмотрите наши последние фото и видео:

**Instagram:** {GALLERY['social_links']['instagram']}
**YouTube:** {GALLERY['social_links']['youtube']}

Здесь вы найдете:
- {GALLERY['promo_content']['photos']['ru']}
- {GALLERY['promo_content']['videos']['ru']}
- {GALLERY['promo_content']['tricks']['ru']}
- {GALLERY['promo_content']['equipment']['ru']}

Следите за нашими обновлениями! ✨
"""
        elif user_lang == 'ar':
            return f"""
📸 **المعرض والفيديو**

شاهد أحدث صورنا وفيديوهاتنا:

**Instagram:** {GALLERY['social_links']['instagram']}
**YouTube:** {GALLERY['social_links']['youtube']}

هنا ستجد:
- {GALLERY['promo_content']['photos']['ar']}
- {GALLERY['promo_content']['videos']['ar']}
- {GALLERY['promo_content']['tricks']['ar']}
- {GALLERY['promo_content']['equipment']['ar']}

تابع تحديثاتنا! ✨
"""
        else:
            return f"""
📸 **GALLERY AND VIDEO**

Check out our latest photos and videos:

**Instagram:** {GALLERY['social_links']['instagram']}
**YouTube:** {GALLERY['social_links']['youtube']}

Here you'll find:
- {GALLERY['promo_content']['photos']['en']}
- {GALLERY['promo_content']['videos']['en']}
- {GALLERY['promo_content']['tricks']['en']}
- {GALLERY['promo_content']['equipment']['en']}

Follow our updates! ✨
"""
    
    def get_locations_text(self, user_id: int) -> str:
        """Получить текст локаций"""
        user_lang = self.language_manager.get_user_language(user_id)
        
        locations_text = ""
        for loc_id, loc_data in LOCATIONS.items():
            name = loc_data['names'].get(user_lang, loc_data['names']['en'])
            description = loc_data['description'].get(user_lang, loc_data['description']['en'])
            
            locations_text += f"📍 **{name}**\n"
            locations_text += f"   - {description}\n"
            locations_text += f"   - 🕒 {loc_data['best_time']}\n\n"
        
        return locations_text