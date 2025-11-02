# handlers/gallery_handlers.py
import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config.constants import States
from handlers.base_handler import BaseHandler
from services.language_manager import LanguageManager
from services.database_service import DatabaseService
from utils.keyboards import KeyboardManager
from services.gallery_service import GalleryService

logger = logging.getLogger(__name__)

class GalleryHandlers(BaseHandler):
    def __init__(self, language_manager: LanguageManager, database_service: DatabaseService,
                 keyboard_manager: KeyboardManager, gallery_service: GalleryService):
        super().__init__(language_manager, database_service, keyboard_manager)
        self.gallery_service = gallery_service
    
    async def start_gallery(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начать галерею"""
        user_id = update.effective_user.id
        await self.database_service.update_user_activity(user_id, 'gallery')
        
        # Показываем категории галереи
        gallery_text = "📸 **ГАЛЕРЕЯ**\n\nВыберите категорию:"
        reply_markup = self.keyboard_manager.get_gallery_categories_keyboard(user_id)
        
        await update.message.reply_text(
            gallery_text,
            parse_mode='Markdown',
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        
        return States.GALLERY_VIEW
    
    async def handle_gallery_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик действий галереи"""
        user_id = update.effective_user.id
        text = update.message.text
        
        menu_texts = self.language_manager.get_all_menu_texts(user_id)
        
        if text == menu_texts['back']:
            return await self._show_main_menu(update, context)
        else:
            return await self.handle_gallery_category(update, context)
    
    async def handle_gallery_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора категории галереи"""
        user_id = update.effective_user.id
        category_name = update.message.text
        
        # Определяем ключ категории по названию
        category_key = None
        categories = self.gallery_service.get_gallery_categories(user_id)
        
        for category in categories:
            if category['name'] == category_name:
                category_key = category['key']
                break
        
        if not category_key:
            await update.message.reply_text(
                "❌ Категория не найдена",
                reply_markup=self.keyboard_manager.get_gallery_categories_keyboard(user_id)
            )
            return States.GALLERY_VIEW
        
        # Получаем контент категории
        media_items = self.gallery_service.get_category_content(category_key, user_id)
        
        if not media_items:
            no_content_text = self._get_no_content_text(user_id)
            await update.message.reply_text(
                no_content_text,
                reply_markup=self.keyboard_manager.get_gallery_categories_keyboard(user_id)
            )
            return States.GALLERY_VIEW
        
        # Сохраняем данные для пагинации
        context.user_data['gallery_items'] = media_items
        context.user_data['gallery_index'] = 0
        context.user_data['gallery_category'] = category_key
        
        # Отправляем первый элемент
        await self._send_media_item(update, context, 0)
        
        return States.GALLERY_VIEW
    
    async def _send_media_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE, index: int):
        """Отправить медиа-элемент"""
        items = context.user_data['gallery_items']
        item = items[index]
        
        caption = f"{item['caption']}\n\n📁 {index + 1}/{len(items)}"
        
        # Создаем клавиатуру пагинации
        keyboard = []
        if index > 0:
            keyboard.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"gallery_prev_{index}"))
        if index < len(items) - 1:
            keyboard.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"gallery_next_{index}"))
        
        keyboard.append(InlineKeyboardButton("Назад ↩️", callback_data="gallery_back"))
        reply_markup = InlineKeyboardMarkup([keyboard])
        
        try:
            if item['type'] == 'photo':
                await update.message.reply_photo(
                    photo=item['url'],
                    caption=caption,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            elif item['type'] == 'video':
                await update.message.reply_video(
                    video=item['url'],
                    caption=caption,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Error sending media: {e}")
            await update.message.reply_text(
                "❌ Ошибка загрузки медиа",
                reply_markup=self.keyboard_manager.get_gallery_categories_keyboard(update.effective_user.id)
            )
    
    async def handle_gallery_pagination(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик пагинации галереи"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = query.from_user.id
        
        if data == "gallery_back":
            await query.edit_message_reply_markup(reply_markup=None)
            return await self.start_gallery(update, context)
        
        elif data.startswith("gallery_prev_"):
            index = int(data.replace("gallery_prev_", "")) - 1
            context.user_data['gallery_index'] = index
            await self._send_media_item(update, context, index)
            
        elif data.startswith("gallery_next_"):
            index = int(data.replace("gallery_next_", "")) + 1
            context.user_data['gallery_index'] = index
            await self._send_media_item(update, context, index)
        
        return States.GALLERY_VIEW
    
    def _get_no_content_text(self, user_id: int) -> str:
        """Получить текст при отсутствии контента"""
        user_lang = self.language_manager.get_user_language(user_id)
        
        if user_lang == 'ru':
            return "📭 В этой категории пока нет контента\n\nСледите за нашими обновлениями в соцсетях! ✨"
        elif user_lang == 'ar':
            return "📭 لا يوجد محتوى في هذه الفئة بعد\n\nتابع تحديثاتنا على وسائل التواصل الاجتماعي! ✨"
        else:
            return "📭 No content in this category yet\n\nFollow our updates on social media! ✨"
    
    async def _show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать главное меню"""
        user_id = update.effective_user.id
        await update.message.reply_text(
            "Возврат в главное меню",
            reply_markup=self.keyboard_manager.get_main_menu(user_id)
        )
        return States.MAIN_MENU
