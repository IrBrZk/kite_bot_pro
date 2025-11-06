# services/ai_assistant.py
import logging
import asyncio

logger = logging.getLogger(__name__)

class AIAssistant:
    def __init__(self):
        pass
    
    async def detect_language(self, text: str) -> str:
        """Упрощенное определение языка"""
        try:
            text_lower = text.lower()
            
            # Русский язык
            russian_chars = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
            if any(char in russian_chars for char in text_lower):
                return 'ru'
            
            # Арабский язык
            arabic_chars = set('ابتثجحخدذرزسشصضطظعغفقكلمنهوي')
            arabic_words = ['مرحبا', 'اهلا', 'شكرا', 'السلام', 'عليكم']
            if any(char in arabic_chars for char in text_lower) or any(word in text_lower for word in arabic_words):
                return 'ar'
            
            # Испанский язык
            spanish_words = ['hola', 'gracias', 'por favor', 'buenos', 'días']
            if any(word in text_lower for word in spanish_words):
                return 'es'
            
            return 'en'
            
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return 'en'
    
    async def translate_text(self, text: str, target_language: str, context: str = "") -> str:
        return text
    
    async def _make_ai_request(self, prompt: str) -> str:
        return "en"