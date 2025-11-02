# services/gallery_service.py
import logging
from typing import Dict, List
from config.settings import GALLERY

logger = logging.getLogger(__name__)

class GalleryService:
    def __init__(self, language_manager):
        self.language_manager = language_manager
        self.media_content = self._initialize_media_content()
    
    def _initialize_media_content(self) -> Dict:
        """Инициализировать медиа контент"""
        return {
            'photos': [
                {'id': 1, 'type': 'photo', 'caption_key': 'photos', 'url': 'https://example.com/photo1.jpg'},
                {'id': 2, 'type': 'photo', 'caption_key': 'photos', 'url': 'https://example.com/photo2.jpg'},
            ],
            'videos': [
                {'id': 1, 'type': 'video', 'caption_key': 'videos', 'url': 'https://example.com/video1.mp4'},
                {'id': 2, 'type': 'video', 'caption_key': 'videos', 'url': 'https://example.com/video2.mp4'},
            ],
            'tricks': [
                {'id': 1, 'type': 'video', 'caption_key': 'tricks', 'url': 'https://example.com/trick1.mp4'},
            ],
            'equipment': [
                {'id': 1, 'type': 'photo', 'caption_key': 'equipment', 'url': 'https://example.com/gear1.jpg'},
            ]
        }
    
    def get_gallery_categories(self, user_id: int) -> List[Dict]:
        """Получить категории галереи"""
        user_lang = self.language_manager.get_user_language(user_id)
        
        categories = []
        for category, items in self.media_content.items():
            if items:  # Только категории с контентом
                category_text = GALLERY['promo_content'][category].get(user_lang, 'en')
                categories.append({
                    'key': category,
                    'name': category_text,
                    'count': len(items)
                })
        
        return categories
    
    def get_category_content(self, category: str, user_id: int) -> List[Dict]:
        """Получить контент категории"""
        user_lang = self.language_manager.get_user_language(user_id)
        items = self.media_content.get(category, [])
        
        for item in items:
            item['caption'] = GALLERY['promo_content'][item['caption_key']].get(user_lang, 'en')
        
        return items
    
    def add_media(self, category: str, media_type: str, url: str, description: str = ""):
        """Добавить новый медиа контент (для админа)"""
        if category not in self.media_content:
            self.media_content[category] = []
        
        new_id = len(self.media_content[category]) + 1
        new_media = {
            'id': new_id,
            'type': media_type,
            'url': url,
            'description': description,
            'added_at': datetime.now().isoformat()
        }
        
        self.media_content[category].append(new_media)
        logger.info(f"✅ Media added to {category}: {url}")
    
    def get_social_links_text(self, user_id: int) -> str:
        """Получить текст с социальными ссылками"""
        user_lang = self.language_manager.get_user_language(user_id)
        
        if user_lang == 'ru':
            return f"""
📱 **ПОДПИШИТЕСЬ НА НАС:**

📸 **Instagram:** {GALLERY['social_links']['instagram']}
🎥 **YouTube:** {GALLERY['social_links']['youtube']}
🎵 **TikTok:** {GALLERY['social_links']['tiktok']}

Следите за нашими обновлениями! ✨
"""
        elif user_lang == 'ar':
            return f"""
📱 **تابعنا على:**

📸 **Instagram:** {GALLERY['social_links']['instagram']}
🎥 **YouTube:** {GALLERY['social_links']['youtube']}
🎵 **TikTok:** {GALLERY['social_links']['tiktok']}

تابع تحديثاتنا! ✨
"""
        else:
            return f"""
📱 **FOLLOW US:**

📸 **Instagram:** {GALLERY['social_links']['instagram']}
🎥 **YouTube:** {GALLERY['social_links']['youtube']}
🎵 **TikTok:** {GALLERY['social_links']['tiktok']}

Follow our updates! ✨
"""