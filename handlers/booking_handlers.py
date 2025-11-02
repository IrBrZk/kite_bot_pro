# handlers/booking_handlers.py
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config.constants import States
from handlers.base_handler import BaseHandler
from services.language_manager import LanguageManager
from services.database_service import DatabaseService
from utils.keyboards import KeyboardManager
from services.booking_service import BookingService
from services.calendar_service import CalendarService

logger = logging.getLogger(__name__)

class BookingHandlers(BaseHandler):
    def __init__(self, language_manager: LanguageManager, database_service: DatabaseService, 
                 keyboard_manager: KeyboardManager, booking_service: BookingService, 
                 calendar_service: CalendarService):
        super().__init__(language_manager, database_service, keyboard_manager)
        self.booking_service = booking_service
        self.calendar_service = calendar_service
    
    async def start_booking(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начать процесс бронирования"""
        user_id = update.effective_user.id
        await self.database_service.update_user_activity(user_id, 'start_booking')
        
        # Показываем календарь
        choose_date_text = self.language_manager.get_text(user_id, 'booking.choose_date')
        keyboard = self.calendar_service.get_calendar_keyboard()
        
        await update.message.reply_text(
            choose_date_text,
            reply_markup=keyboard
        )
        
        return States.BOOKING_DATE
    
    async def show_time_selection(self, query, context, date: str):
        """Показать выбор времени"""
        user_id = query.from_user.id
        
        choose_time_text = self.language_manager.get_text(user_id, 'booking.choose_time')
        reply_markup = self.keyboard_manager.get_times_keyboard()
        
        await query.edit_message_text(
            choose_time_text,
            reply_markup=reply_markup
        )
        
        return States.BOOKING_TIME
    
    async def handle_calendar_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback от календаря"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if data.startswith('calendar_'):
            # Навигация по календарю
            if data == "calendar_current":
                return States.BOOKING_DATE
            
            parts = data.split('_')
            if len(parts) == 3:
                year, month = int(parts[1]), int(parts[2])
                keyboard = self.calendar_service.get_calendar_keyboard(year, month)
                await query.edit_message_reply_markup(reply_markup=keyboard)
        
        elif data.startswith('book_date_'):
            # Выбор даты
            date = data.replace('book_date_', '')
            if self.calendar_service.is_date_available(date):
                context.user_data['booking_date'] = date
                return await self.show_time_selection(query, context, date)
        
        elif data == 'cancel_booking':
            # Отмена бронирования
            await query.edit_message_text("❌ Бронирование отменено")
            return await self._show_main_menu(update, context)
        
        return States.BOOKING_DATE
    
    async def handle_time_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора времени"""
        user_id = update.effective_user.id
        selected_time = update.message.text
        
        # Сохраняем время в контексте
        context.user_data['booking_time'] = selected_time
        
        # Запрашиваем выбор локации
        choose_location_text = self.language_manager.get_text(user_id, 'booking.choose_location')
        reply_markup = self.keyboard_manager.get_locations_keyboard(user_id)
        
        await update.message.reply_text(
            choose_location_text,
            reply_markup=reply_markup
        )
        
        return States.BOOKING_LOCATION_CHOICE
    
    async def handle_location_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора локации"""
        user_id = update.effective_user.id
        selected_location_text = update.message.text
        
        # Определяем ID локации по названию
        location_id = None
        user_lang = self.language_manager.get_user_language(user_id)
        
        from config.settings import LOCATIONS
        for loc_id, loc_data in LOCATIONS.items():
            if loc_data['names'].get(user_lang) == selected_location_text:
                location_id = loc_id
                break
        
        if not location_id:
            location_id = 'dubai'  # По умолчанию
        
        context.user_data['booking_location'] = location_id
        
        # Запрашиваем имя
        enter_name_text = self.language_manager.get_text(user_id, 'booking.enter_name')
        reply_markup = self.keyboard_manager.get_back_keyboard(user_id)
        
        await update.message.reply_text(
            enter_name_text,
            reply_markup=reply_markup
        )
        
        return States.BOOKING_NAME
    
    async def handle_name_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ввода имени"""
        user_id = update.effective_user.id
        user_name = update.message.text
        
        # Сохраняем имя в контексте
        context.user_data['booking_name'] = user_name
        
        # Показываем подтверждение
        booking_data = context.user_data
        confirmation_text = self._format_booking_confirmation(user_id, booking_data)
        reply_markup = self.keyboard_manager.get_confirmation_keyboard(user_id)
        
        await update.message.reply_text(
            confirmation_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return States.BOOKING_CONFIRM
    
    async def handle_booking_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик подтверждения бронирования"""
        user_id = update.effective_user.id
        user_response = update.message.text
        
        user_lang = self.language_manager.get_user_language(user_id)
        
        # Проверяем ответ пользователя
        if any(word in user_response.lower() for word in ['confirm', 'подтвердить', 'تأكيد']):
            # Создаем бронирование
            booking_data = context.user_data
            booking = self.booking_service.create_booking(
                user_id=user_id,
                date=booking_data['booking_date'],
                time=booking_data['booking_time'],
                location=booking_data['booking_location'],
                user_name=booking_data['booking_name']
            )
            
            if booking:
                # Обновляем статистику пользователя
                await self.database_service.increment_bookings(user_id)
                
                # Показываем детали бронирования
                booking_details = self.booking_service.format_booking_details(booking, user_lang)
                confirm_text = self.language_manager.get_text(user_id, 'booking.confirm_booking')
                
                await update.message.reply_text(
                    f"🎉 {confirm_text}\\n{booking_details}",
                    parse_mode='Markdown',
                    reply_markup=self.keyboard_manager.get_main_menu(user_id)
                )
                
                # Очищаем данные
                context.user_data.clear()
                
                return States.MAIN_MENU
            else:
                error_text = self.language_manager.get_text(user_id, 'errors.saving_error')
                await update.message.reply_text(
                    error_text,
                    reply_markup=self.keyboard_manager.get_main_menu(user_id)
                )
                return States.MAIN_MENU
        else:
            # Отмена бронирования
            await update.message.reply_text(
                "❌ Бронирование отменено",
                reply_markup=self.keyboard_manager.get_main_menu(user_id)
            )
            return States.MAIN_MENU
    
    def _format_booking_confirmation(self, user_id: int, booking_data: dict) -> str:
        """Форматировать текст подтверждения бронирования"""
        user_lang = self.language_manager.get_user_language(user_id)
        
        from config.settings import LOCATIONS
        location_name = LOCATIONS[booking_data['booking_location']]['names'].get(user_lang, 'en')
        
        if user_lang == 'ru':
            return f"""
📋 **ПОДТВЕРЖДЕНИЕ БРОНИРОВАНИЯ**

👤 Имя: {booking_data['booking_name']}
📅 Дата: {booking_data['booking_date']}
🕐 Время: {booking_data['booking_time']}
📍 Локация: {location_name}

✅ Подтвердить или ❌ Отменить?
"""
        elif user_lang == 'ar':
            return f"""
📋 **تأكيد الحجز**

👤 الاسم: {booking_data['booking_name']}
📅 التاريخ: {booking_data['booking_date']}
🕐 الوقت: {booking_data['booking_time']}
📍 الموقع: {location_name}

✅ تأكيد أو ❌ إلغاء؟
"""
        else:
            return f"""
📋 **BOOKING CONFIRMATION**

👤 Name: {booking_data['booking_name']}
📅 Date: {booking_data['booking_date']}
🕐 Time: {booking_data['booking_time']}
📍 Location: {location_name}

✅ Confirm or ❌ Cancel?
"""
    
    async def _show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать главное меню"""
        user_id = update.effective_user.id
        await update.message.reply_text(
            "Возврат в главное меню",
            reply_markup=self.keyboard_manager.get_main_menu(user_id)
        )
        return States.MAIN_MENU
