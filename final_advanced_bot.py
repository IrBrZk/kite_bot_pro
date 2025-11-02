cat > /opt/kite_bot_pro/final_advanced_bot.py << 'EOF'
#!/usr/bin/env python3
# final_advanced_bot.py - бот с полной системой статусов слотов
import logging
import os
import requests
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
from enum import Enum

from config.settings import TELEGRAM_BOT_TOKEN, LOCATIONS, SCHEDULE
from config.constants import States
from services.language_manager import LanguageManager
from services.database_service import DatabaseService

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Статусы бронирований
class SlotStatus(Enum):
    AVAILABLE = "available"      # 🟢 Свободен
    BOOKED = "booked"           # 🟡 Забронирован пользователем
    CONFIRMED = "confirmed"     # 🔵 Подтвержден админом
    COMPLETED = "completed"     # ✅ Отработан
    PAID = "paid"               # 💰 Отработан и оплачен
    UNAVAILABLE = "unavailable" # ❌ Недоступен

# Глобальные сервисы
language_manager = LanguageManager()
database_service = DatabaseService()

class AdvancedBookingService:
    def __init__(self, database_service):
        self.database_service = database_service
        self.bookings = {}  # Временное хранилище
        
    def get_slot_status(self, date: str, time: str) -> SlotStatus:
        """Получить статус слота"""
        # Проверяем есть ли бронирование на этот слот
        slot_key = f"{date}_{time}"
        for booking_id, booking in self.bookings.items():
            if booking['date'] == date and booking['time'] == time:
                return SlotStatus(booking['status'])
        
        # Демо: 80% свободных, 20% занятых
        import random
        if random.random() < 0.8:
            return SlotStatus.AVAILABLE
        else:
            return random.choice([SlotStatus.BOOKED, SlotStatus.CONFIRMED])
    
    def get_time_slots_keyboard(self, date: str, user_id: int, is_admin: bool = False):
        """Создать клавиатуру выбора времени с цветовой индикацией статусов"""
        keyboard = []
        
        # Группируем время по периодам
        morning_slots = [t for t in SCHEDULE['time_slots'] if int(t.split(':')[0]) < 12]
        afternoon_slots = [t for t in SCHEDULE['time_slots'] if 12 <= int(t.split(':')[0]) < 17]
        evening_slots = [t for t in SCHEDULE['time_slots'] if int(t.split(':')[0]) >= 17]
        
        # Заголовок с датой
        formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
        keyboard.append([InlineKeyboardButton(f"📅 {formatted_date}", callback_data="ignore")])
        
        # Утренние слоты
        morning_row = []
        for time in morning_slots:
            status = self.get_slot_status(date, time)
            label = self._get_slot_label(time, status, is_admin)
            callback_data = f"time_{time}" if status == SlotStatus.AVAILABLE or is_admin else "ignore"
            morning_row.append(InlineKeyboardButton(label, callback_data=callback_data))
            if len(morning_row) == 3:
                keyboard.append(morning_row)
                morning_row = []
        if morning_row:
            keyboard.append(morning_row)
        
        # Дневные слоты
        afternoon_row = []
        for time in afternoon_slots:
            status = self.get_slot_status(date, time)
            label = self._get_slot_label(time, status, is_admin)
            callback_data = f"time_{time}" if status == SlotStatus.AVAILABLE or is_admin else "ignore"
            afternoon_row.append(InlineKeyboardButton(label, callback_data=callback_data))
            if len(afternoon_row) == 3:
                keyboard.append(afternoon_row)
                afternoon_row = []
        if afternoon_row:
            keyboard.append(afternoon_row)
        
        # Вечерние слоты
        evening_row = []
        for time in evening_slots:
            status = self.get_slot_status(date, time)
            label = self._get_slot_label(time, status, is_admin)
            callback_data = f"time_{time}" if status == SlotStatus.AVAILABLE or is_admin else "ignore"
            evening_row.append(InlineKeyboardButton(label, callback_data=callback_data))
        if evening_row:
            keyboard.append(evening_row)
        
        # Легенда статусов
        if is_admin:
            legend = [
                InlineKeyboardButton("🟢 Свободен", callback_data="ignore"),
                InlineKeyboardButton("🟡 Бронь", callback_data="ignore"),
                InlineKeyboardButton("🔵 Подтв.", callback_data="ignore"),
                InlineKeyboardButton("✅ Отраб.", callback_data="ignore"),
                InlineKeyboardButton("💰 Оплач.", callback_data="ignore")
            ]
        else:
            legend = [
                InlineKeyboardButton("🟢 Свободно", callback_data="ignore"),
                InlineKeyboardButton("🟡 Занято", callback_data="ignore")
            ]
        keyboard.append(legend)
        
        # Кнопки навигации
        nav_buttons = [
            InlineKeyboardButton("◀️ Назад к датам", callback_data="back_to_dates"),
            InlineKeyboardButton("❌ Отмена", callback_data="cancel_booking")
        ]
        keyboard.append(nav_buttons)
        
        return InlineKeyboardMarkup(keyboard)
    
    def _get_slot_label(self, time: str, status: SlotStatus, is_admin: bool) -> str:
        """Получить label для слота в зависимости от статуса"""
        time_short = time.replace(':00', '')
        
        if is_admin:
            # Детальные статусы для админа
            status_map = {
                SlotStatus.AVAILABLE: f"🟢{time_short}",
                SlotStatus.BOOKED: f"🟡{time_short}",
                SlotStatus.CONFIRMED: f"🔵{time_short}",
                SlotStatus.COMPLETED: f"✅{time_short}",
                SlotStatus.PAID: f"💰{time_short}",
                SlotStatus.UNAVAILABLE: f"❌{time_short}"
            }
        else:
            # Упрощенные статусы для пользователя
            status_map = {
                SlotStatus.AVAILABLE: f"🟢{time_short}",
                SlotStatus.BOOKED: f"🟡{time_short}",
                SlotStatus.CONFIRMED: f"🟡{time_short}",
                SlotStatus.COMPLETED: f"🟡{time_short}",
                SlotStatus.PAID: f"🟡{time_short}",
                SlotStatus.UNAVAILABLE: f"❌{time_short}"
            }
        
        return status_map.get(status, f"⚪{time_short}")
    
    def get_time_selection_message(self, date: str, is_admin: bool = False):
        """Получить сообщение с инструкцией для выбора времени"""
        formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
        
        if is_admin:
            return f"""
🕐 **Выбор времени для {formatted_date} (АДМИН)**

📍 **Статусы слотов:**
🟢 Свободен - можно бронировать
🟡 Забронирован - ожидает подтверждения  
🔵 Подтвержден - админом
✅ Отработан - занятие проведено
💰 Оплачен - оплата получена
❌ Недоступен - технический перерыв

⏰ **Доступное время:**
• Утренние: 7:00-11:00  
• Дневные: 12:00-16:00
• Вечерние: 17:00-18:00

👇 **Выберите время нажатием на кнопку:**"""
        else:
            return f"""
🕐 **Выберите время для {formatted_date}:**

📍 **Инструкция:**
- Нажмите на кнопку с нужным временем ниже
- Можно выбрать только свободные слоты (🟢)
- Каждый слот = 1 час занятия

⏰ **Доступное время:**
Утренние: 7:00-11:00  
Дневные: 12:00-16:00
Вечерние: 17:00-18:00

👇 **Выберите время нажатием на кнопку:**"""
    
    def create_booking(self, user_id: int, date: str, time: str, location: str, user_name: str):
        """Создать бронирование"""
        booking_id = f"{user_id}_{date.replace('-', '')}_{time.replace(':', '')}"
        
        booking = {
            'id': booking_id,
            'user_id': user_id,
            'user_name': user_name,
            'date': date,
            'time': time,
            'location': location,
            'status': SlotStatus.BOOKED.value,
            'created_at': datetime.now().isoformat(),
            'confirmed_at': None,
            'completed_at': None,
            'paid_at': None
        }
        
        # Сохраняем бронирование
        self.bookings[booking_id] = booking
        logger.info(f"✅ Booking created: {booking_id} - Status: {SlotStatus.BOOKED.value}")
        
        return booking

class AdvancedCalendarService:
    def __init__(self):
        self.openweather_key = os.getenv('OPENWEATHER_KEY')
        self.demo_mode = not self.openweather_key or self.openweather_key == 'your_api_key_here'
        
    def get_wind_forecast(self, date: str):
        """Получить прогноз ветра (демо)"""
        if self.demo_mode:
            import random
            return round(random.uniform(5, 25), 1)
        return None
    
    def generate_calendar(self, year: int = None, month: int = None):
        """Сгенерировать календарь на месяц"""
        now = datetime.now()
        year = year or now.year
        month = month or now.month
        
        first_day = datetime(year, month, 1)
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)
        
        start_weekday = first_day.weekday()
        calendar_days = []
        current_date = first_day - timedelta(days=start_weekday)
        
        for week in range(6):
            week_days = []
            for day in range(7):
                week_days.append({
                    'date': current_date.date(),
                    'is_current_month': current_date.month == month,
                    'is_past': current_date.date() < now.date(),
                    'is_today': current_date.date() == now.date()
                })
                current_date += timedelta(days=1)
            
            if week > 3 and all(not day['is_current_month'] for day in week_days):
                break
                
            calendar_days.append(week_days)
        
        return {
            'year': year,
            'month': month,
            'month_name': first_day.strftime('%B %Y'),
            'days': calendar_days
        }
    
    def get_wind_quality(self, wind_speed: float):
        """Определить качество ветра"""
        if wind_speed is None:
            return "⚪", "нет данных"
        elif wind_speed < 8:
            return "🔴", "слабый"
        elif 12 <= wind_speed <= 20:
            return "🟢", "идеальный"
        elif wind_speed > 25:
            return "🔴", "сильный"
        else:
            return "🟡", "хороший"
    
    def get_calendar_keyboard(self, year: int = None, month: int = None):
        """Создать клавиатуру календаря"""
        calendar_data = self.generate_calendar(year, month)
        
        keyboard = []
        
        # Заголовок с навигацией
        prev_month = calendar_data['month'] - 1 if calendar_data['month'] > 1 else 12
        prev_year = calendar_data['year'] if calendar_data['month'] > 1 else calendar_data['year'] - 1
        next_month = calendar_data['month'] + 1 if calendar_data['month'] < 12 else 1
        next_year = calendar_data['year'] if calendar_data['month'] < 12 else calendar_data['year'] + 1
        
        header_buttons = [
            InlineKeyboardButton("◀️", callback_data=f"calendar_{prev_year}_{prev_month}"),
            InlineKeyboardButton(calendar_data['month_name'], callback_data="calendar_current"),
            InlineKeyboardButton("▶️", callback_data=f"calendar_{next_year}_{next_month}")
        ]
        keyboard.append(header_buttons)
        
        # Дни недели
        week_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        keyboard.append([InlineKeyboardButton(day, callback_data="ignore") for day in week_days])
        
        # Дни месяца
        for week in calendar_data['days']:
            week_buttons = []
            for day_data in week:
                date_str = day_data['date'].strftime("%Y-%m-%d")
                day_num = day_data['date'].day
                month_num = day_data['date'].month
                date_label = f"{day_num}/{month_num}"
                
                if not day_data['is_current_month']:
                    week_buttons.append(InlineKeyboardButton(f"⚫{date_label}", callback_data="ignore"))
                elif day_data['is_past']:
                    week_buttons.append(InlineKeyboardButton(f"❌{date_label}", callback_data="ignore"))
                else:
                    wind_speed = self.get_wind_forecast(date_str)
                    wind_emoji, wind_quality = self.get_wind_quality(wind_speed)
                    
                    if wind_speed is not None:
                        if wind_quality == "идеальный":
                            label = f"🟢{date_label}🌪"
                        elif wind_quality == "слабый":
                            label = f"🔴{date_label}"
                        elif wind_quality == "сильный":
                            label = f"🔴{date_label}💨"
                        else:
                            label = f"🟡{date_label}"
                    else:
                        label = f"⚪{date_label}"
                    
                    if day_data['is_today']:
                        label = f"📅{date_label}"
                    
                    week_buttons.append(InlineKeyboardButton(label, callback_data=f"book_date_{date_str}"))
            keyboard.append(week_buttons)
        
        # Легенда
        legend_buttons = [
            InlineKeyboardButton("🟢 Идеально", callback_data="ignore"),
            InlineKeyboardButton("🟡 Хорошо", callback_data="ignore"),
            InlineKeyboardButton("🔴 Слабо/Сильно", callback_data="ignore")
        ]
        keyboard.append(legend_buttons)
        
        keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_booking")])
        
        return InlineKeyboardMarkup(keyboard)

# Инициализация сервисов
calendar_service = AdvancedCalendarService()
booking_service = AdvancedBookingService(database_service)

# Проверка админа
def is_admin(user_id: int) -> bool:
    ADMIN_IDS = [224853932]  # Замените на ваш ID
    return user_id in ADMIN_IDS

# Базовые функции клавиатур
def get_main_menu(user_id: int):
    texts = language_manager.get_all_menu_texts(user_id)
    keyboard = [
        [texts['booking'], texts['level_test']],
        [texts['locations'], texts['safety']],
        [texts['contacts'], texts['gallery']],
        [texts['language']]
    ]
    
    if is_admin(user_id):
        keyboard.insert(0, ["🛠️ Админ-панель"])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_language_keyboard():
    from config.constants import SUPPORTED_LANGUAGES
    languages = list(SUPPORTED_LANGUAGES.values())
    keyboard = [
        [languages[0], languages[1]],
        [languages[2]]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_back_keyboard(user_id: int):
    back_text = language_manager.get_text(user_id, 'menu.back')
    return ReplyKeyboardMarkup([[back_text]], resize_keyboard=True)

def get_locations_keyboard(user_id: int):
    user_lang = language_manager.get_user_language(user_id)
    keyboard = []
    for loc_id, loc_data in LOCATIONS.items():
        location_name = loc_data['names'].get(user_lang, loc_data['names']['en'])
        keyboard.append([location_name])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_confirmation_keyboard(user_id: int):
    user_lang = language_manager.get_user_language(user_id)
    if user_lang == 'ru':
        confirm_text, cancel_text = "✅ Подтвердить", "❌ Отменить"
    elif user_lang == 'ar':
        confirm_text, cancel_text = "✅ تأكيد", "❌ إلغاء"
    else:
        confirm_text, cancel_text = "✅ Confirm", "❌ Cancel"
    return ReplyKeyboardMarkup([[confirm_text, cancel_text]], resize_keyboard=True)

# Основные обработчики
async def start(update, context):
    user = update.effective_user
    user_id = user.id
    logger.info(f"👋 User: {user_id} - {user.first_name}")

    user_obj = await database_service.get_user(user_id)
    if not user_obj:
        user_obj = await database_service.create_user(user)
    
    welcome_text = language_manager.get_text(user_id, 'welcome.personalized')
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu(user_id),
        parse_mode='Markdown'
    )
    return States.MAIN_MENU

async def handle_main_menu(update, context):
    user_id = update.effective_user.id
    text = update.message.text
    menu_texts = language_manager.get_all_menu_texts(user_id)
    
    logger.info(f"📝 User {user_id} selected: {text}")
    
    if text == menu_texts['booking']:
        return await start_booking(update, context)
    elif text == "🛠️ Админ-панель" and is_admin(user_id):
        await update.message.reply_text("🛠️ Админ-панель в разработке...")
    elif text == menu_texts['level_test']:
        await update.message.reply_text("🎯 Тест уровня в разработке...")
    elif text == menu_texts['gallery']:
        await update.message.reply_text("📸 Галерея в разработке...")
    elif text == menu_texts['safety']:
        await update.message.reply_text("🛟 Правила безопасности в разработке...")
    elif text == menu_texts['language']:
        await update.message.reply_text("🌐 Выберите язык:", reply_markup=get_language_keyboard())
        return States.LANGUAGE_SELECTION
    elif text == menu_texts['contacts']:
        await handle_contacts(update, context)
    elif text == menu_texts['locations']:
        await handle_locations(update, context)
    else:
        await update.message.reply_text("❌ Неизвестная команда")
    return States.MAIN_MENU

async def start_booking(update, context):
    user_id = update.effective_user.id
    context.user_data.clear()
    
    status_note = "🌪️ *Реальный прогноз ветра*" if not calendar_service.demo_mode else "🎭 *Демо-режим*"
    choose_date_text = f"{language_manager.get_text(user_id, 'booking.choose_date')}\\n\\n{status_note}"
    
    keyboard = calendar_service.get_calendar_keyboard()
    await update.message.reply_text(choose_date_text, reply_markup=keyboard, parse_mode='Markdown')
    return States.BOOKING_DATE

async def handle_calendar_callback(update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if data.startswith('calendar_'):
        if data == "calendar_current": return
        parts = data.split('_')
        if len(parts) == 3:
            try:
                year, month = int(parts[1]), int(parts[2])
                keyboard = calendar_service.get_calendar_keyboard(year, month)
                await query.edit_message_text(
                    query.message.text,
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Calendar error: {e}")
                await query.answer("❌ Ошибка календаря", show_alert=True)
    
    elif data.startswith('book_date_'):
        date = data.replace('book_date_', '')
        context.user_data['booking_date'] = date
        
        # Получаем клавиатуру времени с учетом статусов
        admin_mode = is_admin(user_id)
        time_keyboard = booking_service.get_time_slots_keyboard(date, user_id, admin_mode)
        time_message = booking_service.get_time_selection_message(date, admin_mode)
        
        await query.edit_message_text(
            time_message,
            reply_markup=time_keyboard,
            parse_mode='Markdown'
        )
        return States.BOOKING_TIME
    
    elif data == 'cancel_booking' or data == 'back_to_dates':
        await query.edit_message_text("❌ Бронирование отменено")
        return await show_main_menu(update, context)
    
    elif data.startswith('time_'):
        time = data.replace('time_', '')
        await handle_time_selection_callback(update, context, time)

async def handle_time_selection_callback(update, context, selected_time: str):
    """Обработчик выбора времени через callback"""
    query = update.callback_query
    user_id = query.from_user.id
    
    date = context.user_data.get('booking_date')
    if not date:
        await query.answer("❌ Ошибка: дата не выбрана", show_alert=True)
        return
    
    slot_status = booking_service.get_slot_status(date, selected_time)
    
    # Пользователь может выбрать только свободные слоты
    if not is_admin(user_id) and slot_status != SlotStatus.AVAILABLE:
        await query.answer("❌ Это время уже занято", show_alert=True)
        return
    
    context.user_data['booking_time'] = selected_time
    await query.answer(f"✅ Выбрано время: {selected_time}")
    
    # Переходим к выбору локации
    choose_location_text = language_manager.get_text(user_id, 'booking.choose_location')
    await query.message.reply_text(
        choose_location_text,
        reply_markup=get_locations_keyboard(user_id)
    )
    
    return States.BOOKING_LOCATION_CHOICE

async def show_main_menu(update, context):
    user_id = update.effective_user.id if hasattr(update, 'effective_user') else update.callback_query.from_user.id
    
    if hasattr(update, 'callback_query'):
        await update.callback_query.message.reply_text("Возврат в главное меню", reply_markup=get_main_menu(user_id))
    else:
        await update.message.reply_text("Возврат в главное меню", reply_markup=get_main_menu(user_id))
    return States.MAIN_MENU

async def handle_location_selection(update, context):
    user_id = update.effective_user.id
    selected_location_text = update.message.text
    user_lang = language_manager.get_user_language(user_id)
    
    location_id = None
    for loc_id, loc_data in LOCATIONS.items():
        if loc_data['names'].get(user_lang) == selected_location_text:
            location_id = loc_id
            break
    
    if location_id:
        context.user_data['booking_location'] = location_id
        enter_name_text = language_manager.get_text(user_id, 'booking.enter_name')
        await update.message.reply_text(enter_name_text, reply_markup=get_back_keyboard(user_id))
        return States.BOOKING_NAME
    else:
        await update.message.reply_text("❌ Неверная локация", reply_markup=get_locations_keyboard(user_id))
        return States.BOOKING_LOCATION_CHOICE

async def handle_name_input(update, context):
    user_id = update.effective_user.id
    user_name = update.message.text.strip()
    
    if len(user_name) < 2:
        await update.message.reply_text("❌ Имя слишком короткое", reply_markup=get_back_keyboard(user_id))
        return States.BOOKING_NAME
    
    context.user_data['booking_name'] = user_name
    confirmation_text = format_booking_confirmation(user_id, context.user_data)
    await update.message.reply_text(confirmation_text, reply_markup=get_confirmation_keyboard(user_id), parse_mode='Markdown')
    return States.BOOKING_CONFIRM

def format_booking_confirmation(user_id: int, booking_data: dict) -> str:
    user_lang = language_manager.get_user_language(user_id)
    location_name = LOCATIONS[booking_data['booking_location']]['names'].get(user_lang, 'en')
    
    booking_date = datetime.strptime(booking_data['booking_date'], "%Y-%m-%d")
    formatted_date = booking_date.strftime("%d.%m.%Y")
    
    if user_lang == 'ru':
        return f"""📋 **ПОДТВЕРЖДЕНИЕ БРОНИРОВАНИЯ**

👤 Имя: {booking_data['booking_name']}
📅 Дата: {formatted_date}
🕐 Время: {booking_data['booking_time']}
📍 Локация: {location_name}

🎯 **Статус:** 🟡 Ожидает подтверждения

✅ Подтвердить или ❌ Отменить?"""
    elif user_lang == 'ar':
        return f"""📋 **تأكيد الحجز**

👤 الاسم: {booking_data['booking_name']}
📅 التاريخ: {formatted_date}
🕐 الوقت: {booking_data['booking_time']}
📍 الموقع: {location_name}

🎯 **الحالة:** 🟡 في انتظار التأكيد

✅ تأكيد أو ❌ إلغاء؟"""
    else:
        return f"""📋 **BOOKING CONFIRMATION**

👤 Name: {booking_data['booking_name']}
📅 Date: {formatted_date}
🕐 Time: {booking_data['booking_time']}
📍 Location: {location_name}

🎯 **Status:** 🟡 Pending confirmation

✅ Confirm or ❌ Cancel?"""

async def handle_booking_confirmation(update, context):
    user_id = update.effective_user.id
    user_response = update.message.text
    user_lang = language_manager.get_user_language(user_id)
    
    confirm_keywords = ['confirm', 'подтвердить', 'تأكيد']
    cancel_keywords = ['cancel', 'отменить', 'إلغاء']
    
    if any(keyword in user_response.lower() for keyword in confirm_keywords):
        booking_data = context.user_data
        booking = booking_service.create_booking(
            user_id=user_id,
            date=booking_data['booking_date'],
            time=booking_data['booking_time'],
            location=booking_data['booking_location'],
            user_name=booking_data['booking_name']
        )
        
        if booking:
            booking_details = format_booking_details(booking, user_lang)
            await update.message.reply_text(f"🎉 Бронирование создано!\\n{booking_details}", parse_mode='Markdown', reply_markup=get_main_menu(user_id))
            context.user_data.clear()
            return States.MAIN_MENU
        else:
            await update.message.reply_text("❌ Ошибка сохранения", reply_markup=get_main_menu(user_id))
            return States.MAIN_MENU
            
    elif any(keyword in user_response.lower() for keyword in cancel_keywords):
        cancel_text = "❌ Бронирование отменено"
        await update.message.reply_text(cancel_text, reply_markup=get_main_menu(user_id))
        return States.MAIN_MENU
    else:
        await update.message.reply_text("❌ Подтвердите или отмените", reply_markup=get_confirmation_keyboard(user_id))
        return States.BOOKING_CONFIRM

def format_booking_details(booking: dict, language: str) -> str:
    location_name = LOCATIONS[booking['location']]['names'].get(language, 'en')
    
    booking_date = datetime.strptime(booking['date'], "%Y-%m-%d")
    formatted_date = booking_date.strftime("%d.%m.%Y")
    
    if language == 'ru':
        return f"""
📅 **ВАША ЗАПИСЬ:**

👤 Имя: {booking['user_name']}
📅 Дата: {formatted_date}
🕐 Время: {booking['time']}
📍 Локация: {location_name}
🎯 Статус: 🟡 Забронировано

📞 **Абдула свяжется с вами для подтверждения**
⏰ Время связи: с 7:00 до 18:00

Сохраните эту информацию! ✨"""
    else:
        return f"""
📅 **YOUR BOOKING:**

👤 Name: {booking['user_name']}
📅 Date: {formatted_date}
🕐 Time: {booking['time']}
📍 Location: {location_name}
🎯 Status: 🟡 Booked

📞 **Abdula will contact you to confirm**
⏰ Contact hours: 7:00 AM to 6:00 PM

Save this information! ✨"""

# Остальные обработчики
async def handle_language_selection(update, context):
    user_id = update.effective_user.id
    text = update.message.text
    
    language_map = {'English 🇺🇸': 'en', 'Russian 🇷🇺': 'ru', 'Arabic 🇦🇪': 'ar'}
    language_code = language_map.get(text, 'en')
    
    language_manager.set_user_language(user_id, language_code)
    user = await database_service.get_user(user_id)
    if user:
        user.language = language_code
        user.language_selected = True
        await database_service.update_user(user)
    
    if language_code == 'ru': confirmation = "✅ Язык изменен на русский"
    elif language_code == 'ar': confirmation = "✅ تم تغيير اللغة إلى العربية"
    else: confirmation = "✅ Language changed to English"
    
    await update.message.reply_text(confirmation, reply_markup=get_main_menu(user_id))
    return States.MAIN_MENU

async def handle_contacts(update, context):
    user_id = update.effective_user.id
    user_lang = language_manager.get_user_language(user_id)
    from config.settings import CONTACTS
    
    if user_lang == 'ru':
        contacts_text = f"""📞 **КОНТАКТЫ АБДУЛЫ:**

**Телефон:** {CONTACTS['phone']}
**Telegram:** {CONTACTS['telegram']}
**Instagram:** {CONTACTS['instagram']}

🕒 **Часы работы:**
{CONTACTS['support_hours']}"""
    else:
        contacts_text = f"""📞 **ABDULA'S CONTACTS:**

**Phone:** {CONTACTS['phone']}
**Telegram:** {CONTACTS['telegram']}
**Instagram:** {CONTACTS['instagram']}

🕒 **Working hours:**
{CONTACTS['support_hours']}"""
    
    await update.message.reply_text(contacts_text, parse_mode='Markdown', reply_markup=get_main_menu(user_id))

async def handle_locations(update, context):
    user_id = update.effective_user.id
    user_lang = language_manager.get_user_language(user_id)
    from config.settings import LOCATIONS
    
    locations_text = ""
    for loc_id, loc_data in LOCATIONS.items():
        name = loc_data['names'].get(user_lang, loc_data['names']['en'])
        description = loc_data['description'].get(user_lang, loc_data['description']['en'])
        locations_text += f"📍 **{name}**\\n   - {description}\\n   - 🕒 {loc_data['best_time']}\\n\\n"
    
    await update.message.reply_text(locations_text, parse_mode='Markdown', reply_markup=get_main_menu(user_id))

async def cancel(update, context):
    user_id = update.effective_user.id
    user_lang = language_manager.get_user_language(user_id)
    cancel_text = "Операция отменена"
    await update.message.reply_text(cancel_text, reply_markup=get_main_menu(user_id))
    return ConversationHandler.END

async def error_handler(update, context):
    logger.error(f"Ошибка: {context.error}")

def main():
    logger.info("🚀 Kite Bot Pro с расширенной системой статусов запускается...")
    
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(database_service.init_db())
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            States.MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)],
            States.LANGUAGE_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_language_selection)],
            States.BOOKING_DATE: [CallbackQueryHandler(handle_calendar_callback, pattern="^(calendar_|book_date_|cancel_booking|back_to_dates)")],
            States.BOOKING_TIME: [CallbackQueryHandler(handle_calendar_callback, pattern="^(time_.*)")],
            States.BOOKING_LOCATION_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_location_selection)],
            States.BOOKING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name_input)],
            States.BOOKING_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_booking_confirmation)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    
    logger.info("✅ Бот с расширенной системой статусов запущен!")
    application.run_polling()

if __name__ == '__main__':
    main()
EOF