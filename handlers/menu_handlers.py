# handlers/menu_handlers.py
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config.constants import States
from handlers.base_handler import BaseHandler
from services.language_manager import LanguageManager
from services.database_service import DatabaseService
from utils.keyboards import KeyboardManager

logger = logging.getLogger(__name__)

class MenuHandlers(BaseHandler):
    def __init__(self, language_manager: LanguageManager, database_service: DatabaseService, 
                 keyboard_manager: KeyboardManager):
        super().__init__(language_manager, database_service, keyboard_manager)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        user_id = user.id
        
        logger.info(f"👋 User interaction: {user_id} - {user.first_name}")
        
        # Проверяем существующего пользователя
        existing_user = await self.database_service.get_user(user_id)
        
        if existing_user and existing_user.language_selected:
            # Существующий пользователь - берем язык из базы
            language = existing_user.language
            self.language_manager.set_user_language(user_id, language)
            await self.database_service.update_user_activity(user_id, 'start')
            
            welcome_text = self.language_manager.get_text(user_id, 'welcome.returning')
            reply_markup = self.keyboard_manager.get_main_menu(user_id)
            
            await update.message.reply_text(
                welcome_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            return States.MAIN_MENU
        else:
            # Новый пользователь или без выбора языка
            if not existing_user:
                await self.database_service.create_user(user)
            
            # Показываем выбор языка
            return await self.show_language_selection(update, context)
    
    async def show_language_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать выбор языка"""
        user_id = update.effective_user.id
        
        welcome_text = self.language_manager.get_text(user_id, 'welcome.new_user')
        reply_markup = self.keyboard_manager.get_language_keyboard()
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup
        )
        
        return States.LANGUAGE_SELECTION
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать главное меню"""
        user_id = update.effective_user.id
        await self.database_service.update_user_activity(user_id, 'main_menu')
        
        menu_text = self.language_manager.get_text(user_id, 'welcome.personalized')
        reply_markup = self.keyboard_manager.get_main_menu(user_id)
        
        await update.message.reply_text(
            menu_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return States.MAIN_MENU
    
    async def handle_contacts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик контактов"""
        user_id = update.effective_user.id
        await self.database_service.update_user_activity(user_id, 'contacts')
        
        from services.content_manager import ContentManager
        content_manager = ContentManager(self.language_manager)
        contacts_text = content_manager.get_contacts_text(user_id)
        
        await update.message.reply_text(
            contacts_text,
            parse_mode='Markdown',
            reply_markup=self.keyboard_manager.get_main_menu(user_id)
        )
        
        return States.MAIN_MENU
    
    async def handle_locations(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик локаций"""
        user_id = update.effective_user.id
        await self.database_service.update_user_activity(user_id, 'locations')
        
        from services.content_manager import ContentManager
        content_manager = ContentManager(self.language_manager)
        locations_text = content_manager.get_locations_text(user_id)
        
        await update.message.reply_text(
            locations_text,
            parse_mode='Markdown',
            reply_markup=self.keyboard_manager.get_main_menu(user_id)
        )
        
        return States.MAIN_MENU
    
    async def handle_gallery(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик галереи"""
        user_id = update.effective_user.id
        await self.database_service.update_user_activity(user_id, 'gallery')
        
        # Показываем категории галереи
        from services.content_manager import ContentManager
        content_manager = ContentManager(self.language_manager)
        gallery_text = content_manager.get_gallery_text(user_id)
        reply_markup = self.keyboard_manager.get_gallery_categories_keyboard(user_id)
        
        await update.message.reply_text(
            gallery_text,
            parse_mode='Markdown',
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        
        return States.GALLERY_VIEW
    
    async def handle_language_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора языка"""
        user_id = update.effective_user.id
        await self.database_service.update_user_activity(user_id, 'language_select')
        
        text = self.language_manager.get_text(user_id, 'menu.language')
        reply_markup = self.keyboard_manager.get_language_keyboard()
        
        await update.message.reply_text(
            text,
            reply_markup=reply_markup
        )
        
        return States.LANGUAGE_SELECTION
    
    async def change_language(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Сменить язык"""
        user_id = update.effective_user.id
        selected_language = update.message.text
        
        # Определяем код языка по тексту кнопки
        language_map = {
            'English 🇺🇸': 'en',
            'Russian 🇷🇺': 'ru', 
            'Arabic 🇦🇪': 'ar'
        }
        
        language_code = language_map.get(selected_language, 'en')
        
        # Сохраняем в базу и менеджер языка
        await self.database_service.set_user_language(user_id, language_code)
        self.language_manager.set_user_language(user_id, language_code)
        
        # Подтверждение смены языка
        if language_code == 'ru':
            confirmation = "✅ Язык изменен на русский"
        elif language_code == 'ar':
            confirmation = "✅ تم تغيير اللغة إلى العربية"
        else:
            confirmation = "✅ Language changed to English"
        
        await update.message.reply_text(
            confirmation,
            reply_markup=self.keyboard_manager.get_main_menu(user_id)
        )
        
        return States.MAIN_MENU
    
    async def handle_back(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик кнопки Назад"""
        return await self.show_main_menu(update, context)
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена операции"""
        user_id = update.effective_user.id
        await self.database_service.update_user_activity(user_id, 'cancel')
        
        cancel_text = self.language_manager.get_text(user_id, 'menu.home')
        await update.message.reply_text(
            cancel_text,
            reply_markup=self.keyboard_manager.get_main_menu(user_id)
        )
        
        return ConversationHandler.END
