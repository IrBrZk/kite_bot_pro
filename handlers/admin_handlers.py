# handlers/admin_handlers.py
import logging
from telegram import Update
from telegram.ext import ContextTypes
from config.constants import States
from handlers.base_handler import BaseHandler
from services.language_manager import LanguageManager
from services.database_service import DatabaseService
from utils.keyboards import KeyboardManager
from services.admin_service import AdminService

logger = logging.getLogger(__name__)

class AdminHandlers(BaseHandler):
    def __init__(self, language_manager: LanguageManager, database_service: DatabaseService,
                 keyboard_manager: KeyboardManager, admin_service: AdminService):
        super().__init__(language_manager, database_service, keyboard_manager)
        self.admin_service = admin_service
    
    async def handle_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик админ команды"""
        user_id = update.effective_user.id
        
        if not self.admin_service.is_admin(user_id):
            await update.message.reply_text("❌ Доступ запрещен")
            return States.MAIN_MENU
        
        # Показываем админ панель
        admin_text = "🛠️ **АДМИН ПАНЕЛЬ**\\n\\nВыберите действие:"
        reply_markup = self.keyboard_manager.get_admin_keyboard(user_id)
        
        await update.message.reply_text(
            admin_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        return States.MAIN_MENU
    
    async def handle_admin_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик статистики"""
        user_id = update.effective_user.id
        
        if not self.admin_service.is_admin(user_id):
            await update.message.reply_text("❌ Доступ запрещен")
            return States.MAIN_MENU
        
        stats_text = self.admin_service.format_admin_stats(user_id)
        
        await update.message.reply_text(
            stats_text,
            parse_mode='Markdown',
            reply_markup=self.keyboard_manager.get_admin_keyboard(user_id)
        )
    
    async def handle_today_bookings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик сегодняшних бронирований"""
        user_id = update.effective_user.id
        
        if not self.admin_service.is_admin(user_id):
            await update.message.reply_text("❌ Доступ запрещен")
            return States.MAIN_MENU
        
        today_bookings = self.admin_service.get_today_bookings()
        
        if not today_bookings:
            bookings_text = "📅 На сегодня бронирований нет"
        else:
            bookings_text = "📅 **СЕГОДНЯШНИЕ БРОНИРОВАНИЯ:**\\n\\n"
            for booking in today_bookings:
                bookings_text += f"👤 {booking['user_name']}\\n"
                bookings_text += f"🕐 {booking['time']} - {booking['location']}\\n"
                bookings_text += f"📞 ID: {booking['user_id']}\\n"
                bookings_text += "─" * 20 + "\\n"
        
        await update.message.reply_text(
            bookings_text,
            parse_mode='Markdown',
            reply_markup=self.keyboard_manager.get_admin_keyboard(user_id)
        )
