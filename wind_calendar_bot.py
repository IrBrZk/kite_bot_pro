#!/usr/bin/env python3
# wind_calendar_bot.py - бот с AI-ветровым календарем
import logging
import os
import requests
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

from config.settings import TELEGRAM_BOT_TOKEN, LOCATIONS, SCHEDULE
from config.constants import States
from services.language_manager import LanguageManager
from services.database_service import DatabaseService
from services.booking_service import BookingService

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Глобальные сервисы
language_manager = LanguageManager()
database_service = DatabaseService()
booking_service = BookingService(database_service)

class WindCalendarService:
    def __init__(self, booking_service):
        self.booking_service = booking_service
        self.openweather_key = os.getenv('OPENWEATHER_KEY', 'demo_key')  # Замените на ваш ключ
    
    def get_wind_forecast(self, date: str, location: str = "Dubai"):
        """Получить прогноз ветра с OpenWeather"""
        # Для демо - возвращаем случайные значения
        # В реальном использовании раскомментируйте код ниже
        
        # Демо-режим: случайный ветер для тестирования
        import random
        wind_speed = random.uniform(5, 25)
        
        """
        # РЕАЛЬНЫЙ КОД (раскомментируйте когда получите API ключ):
        url = "http://api.openweathermap.org/data/2.5/forecast"
        params = {
            "q": location,
            "appid": self.openweather_key,
            "units": "metric"
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
            
            # Ищем прогнозы на нужную дату в дневное время
            day_forecasts = []
            for item in data.get('list', []):
                forecast_time = datetime.fromtimestamp(item['dt'])
                if (forecast_time.date() == target_date and 
                    10 <= forecast_time.hour <= 18):
                    wind_speed = item['wind']['speed'] * 3.6  # м/с → узлы
                    day_forecasts.append(wind_speed)
            
            if day_forecasts:
                return round(sum(day_forecasts) / len(day_forecasts), 1)
                
        except Exception as e:
            logger.error(f"Wind forecast error: {e}")
        """
        
        return round(wind_speed, 1)
    
    def generate_calendar(self, year: int = None, month: int = None):
        """Сгенерировать календарь на месяц"""
        now = datetime.now()
        year = year or now.year
        month = month or now.month
        
        # Первый день месяца
        first_day = datetime(year, month, 1)
        # Последний день месяца
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)
        
        # Дни недели первого дня
        start_weekday = first_day.weekday()
        
        # Генерация календаря
        calendar_days = []
        current_date = first_day - timedelta(days=start_weekday)
        
        # 6 недель максимум
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
        if wind_speed < 10:
            return "🔴", "слабый"
        elif 12 <= wind_speed <= 18:
            return "🟢", "идеальный"
        elif wind_speed > 20:
            return "🔴", "сильный"
        else:
            return "🟡", "хороший"
    
    def get_calendar_keyboard(self, year: int = None, month: int = None):
        """Создать клавиатуру календаря с прогнозом ветра"""
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
        
        # Дни месяца с прогнозом ветра
        for week in calendar_data['days']:
            week_buttons = []
            for day_data in week:
                date_str = day_data['date'].strftime("%Y-%m-%d")
                day_num = day_data['date'].day
                
                if not day_data['is_current_month']:
                    # Дни другого месяца
                    week_buttons.append(InlineKeyboardButton(" ", callback_data="ignore"))
                elif day_data['is_past']:
                    # Прошедшие дни
                    week_buttons.append(InlineKeyboardButton(f"❌", callback_data="ignore"))
                else:
                    # Доступные дни с прогнозом ветра
                    wind_speed = self.get_wind_forecast(date_str)
                    wind_emoji, wind_quality = self.get_wind_quality(wind_speed)
                    
                    # Создаем label с эмодзи ветра
                    if wind_speed:
                        if wind_quality == "идеальный":
                            label = f"🟢{day_num}🌪{wind_speed}"
                        elif wind_quality == "слабый":
                            label = f"🔴{day_num}"
                        elif wind_quality == "сильный":
                            label = f"🔴{day_num}💨"
                        else:
                            label = f"🟡{day_num}"
                    else:
                        label = str(day_num)
                    
                    # Подсветка сегодняшнего дня
                    if day_data['is_today']:
                        label = f"📅{label}"
                    
                    week_buttons.append(InlineKeyboardButton(
                        label,
                        callback_data=f"book_date_{date_str}"
                    ))
            keyboard.append(week_buttons)
        
        # Легенда ветра
        legend_buttons = [
            InlineKeyboardButton("🟢 Идеально", callback_data="ignore"),
            InlineKeyboardButton("🟡 Хорошо", callback_data="ignore"),
            InlineKeyboardButton("🔴 Слабо/Сильно", callback_data="ignore")
        ]
        keyboard.append(legend_buttons)
        
        # Кнопка отмены
        keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_booking")])
        
        return InlineKeyboardMarkup(keyboard)
    
    def is_date_available(self, date: str):
        """Проверить доступность даты"""
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
            today = datetime.now().date()
            return target_date >= today
        except ValueError:
            return False
    
    def get_wind_description(self, date: str):
        """Получить описание ветра для выбранной даты"""
        wind_speed = self.get_wind_forecast(date)
        if not wind_speed:
            return "Прогноз ветра недоступен"
        
        wind_emoji, wind_quality = self.get_wind_quality(wind_speed)
        
        descriptions = {
            "идеальный": f"🎉 Идеальный день для кайтсерфинга! Ветер {wind_speed} узлов - отличные условия для катания!",
            "хороший": f"👍 Хорошие условия! Ветер {wind_speed} узлов - можно кататься!",
            "слабый": f"⚠️ Слабый ветер {wind_speed} узлов. Возможно, лучше перенести занятие.",
            "сильный": f"🌪️ Сильный ветер {wind_speed} узлов! Только для опытных райдеров."
        }
        
        return f"{wind_emoji} {descriptions.get(wind_quality, 'Проверьте условия на месте')}"

# Инициализация календаря
calendar_service = WindCalendarService(booking_service)

def get_main_menu(user_id: int):
    """Главное меню"""
    texts = language_manager.get_all_menu_texts(user_id)
    
    keyboard = [
        [texts['booking'], texts['level_test']],
        [texts['locations'], texts['safety']],
        [texts['contacts'], texts['gallery']],
        [texts['language']]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_language_keyboard():
    """Клавиатура выбора языка"""
    from config.constants import SUPPORTED_LANGUAGES
    languages = list(SUPPORTED_LANGUAGES.values())
    keyboard = [
        [languages[0], languages[1]],
        [languages[2]]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_back_keyboard(user_id: int):
    """Клавиатура с кнопкой Назад"""
    back_text = language_manager.get_text(user_id, 'menu.back')
    keyboard = [[back_text]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_times_keyboard():
    """Клавиатура со временем"""
    times = SCHEDULE['time_slots']
    
    keyboard = []
    row = []
    for i, time in enumerate(times):
        row.append(time)
        if len(row) == 3 or i == len(times) - 1:
            keyboard.append(row)
            row = []
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_locations_keyboard(user_id: int):
    """Клавиатура с локациями"""
    user_lang = language_manager.get_user_language(user_id)
    
    keyboard = []
    for loc_id, loc_data in LOCATIONS.items():
        location_name = loc_data['names'].get(user_lang, loc_data['names']['en'])
        keyboard.append([location_name])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_confirmation_keyboard(user_id: int):
    """Клавиатура подтверждения"""
    user_lang = language_manager.get_user_language(user_id)
    
    if user_lang == 'ru':
        confirm_text = "✅ Подтвердить"
        cancel_text = "❌ Отменить"
    elif user_lang == 'ar':
        confirm_text = "✅ تأكيد"
        cancel_text = "❌ إلغاء"
    else:
        confirm_text = "✅ Confirm"
        cancel_text = "❌ Cancel"
    
    keyboard = [
        [confirm_text, cancel_text]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update, context):
    """Обработчик команды /start"""
    user = update.effective_user
    user_id = user.id
    
    logger.info(f"👋 User: {user_id} - {user.first_name}")

    # Создаем/получаем пользователя
    user_obj = await database_service.get_user(user_id)
    if not user_obj:
        user_obj = await database_service.create_user(user)
    
    welcome_text = language_manager.get_text(user_id, 'welcome.personalized')
    reply_markup = get_main_menu(user_id)

    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return States.MAIN_MENU

async def handle_main_menu(update, context):
    """Обработка главного меню"""
    user_id = update.effective_user.id
    text = update.message.text
    
    menu_texts = language_manager.get_all_menu_texts(user_id)
    
    logger.info(f"📝 User {user_id} selected: {text}")
    
    if text == menu_texts['booking']:
        return await start_booking(update, context)
    elif text == menu_texts['level_test']:
        await update.message.reply_text("🎯 Тест уровня в разработке...")
    elif text == menu_texts['gallery']:
        await update.message.reply_text("📸 Галерея в разработке...")
    elif text == menu_texts['safety']:
        await update.message.reply_text("🛟 Правила безопасности в разработке...")
    elif text == menu_texts['language']:
        reply_markup = get_language_keyboard()
        await update.message.reply_text("🌐 Выберите язык:", reply_markup=reply_markup)
        return States.LANGUAGE_SELECTION
    elif text == menu_texts['contacts']:
        await handle_contacts(update, context)
    elif text == menu_texts['locations']:
        await handle_locations(update, context)
    else:
        await update.message.reply_text("❌ Неизвестная команда")
    
    return States.MAIN_MENU

async def start_booking(update, context):
    """Начать процесс бронирования"""
    user_id = update.effective_user.id
    
    # Очищаем предыдущие данные
    context.user_data.clear()
    
    choose_date_text = f"{language_manager.get_text(user_id, 'booking.choose_date')}\\n\\n🌪️ *Календарь с прогнозом ветра:*"
    keyboard = calendar_service.get_calendar_keyboard()
    
    await update.message.reply_text(
        choose_date_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    
    return States.BOOKING_DATE

async def handle_calendar_callback(update, context):
    """Обработчик callback от календаря"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    logger.info(f"📅 Calendar callback: {data} from user {user_id}")
    
    if data.startswith('calendar_'):
        # Навигация по календарю
        if data == "calendar_current":
            return
        
        parts = data.split('_')
        if len(parts) == 3:
            try:
                year, month = int(parts[1]), int(parts[2])
                keyboard = calendar_service.get_calendar_keyboard(year, month)
                await query.edit_message_reply_markup(reply_markup=keyboard)
            except (ValueError, TypeError) as e:
                logger.error(f"Error parsing calendar data: {e}")
                await query.answer("❌ Ошибка календаря", show_alert=True)
    
    elif data.startswith('book_date_'):
        # Выбор даты
        date = data.replace('book_date_', '')
        if calendar_service.is_date_available(date):
            context.user_data['booking_date'] = date
            
            # Добавляем описание ветра
            wind_description = calendar_service.get_wind_description(date)
            
            # Переходим к выбору времени
            choose_time_text = f"{language_manager.get_text(user_id, 'booking.choose_time')}\\n\\n{wind_description}"
            reply_markup = get_times_keyboard()
            
            await query.edit_message_text(
                choose_time_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            return States.BOOKING_TIME
        else:
            await query.answer("❌ Эта дата недоступна", show_alert=True)
    
    elif data == 'cancel_booking':
        # Отмена бронирования
        await query.edit_message_text("❌ Бронирование отменено")
        return await show_main_menu(update, context)

async def show_main_menu(update, context):
    """Показать главное меню"""
    if hasattr(update, 'callback_query'):
        user_id = update.callback_query.from_user.id
        await update.callback_query.message.reply_text(
            "Возврат в главное меню",
            reply_markup=get_main_menu(user_id)
        )
    else:
        user_id = update.effective_user.id
        await update.message.reply_text(
            "Возврат в главное меню",
            reply_markup=get_main_menu(user_id)
        )
    return States.MAIN_MENU

# ... остальные функции остаются такими же как в предыдущей версии ...

async def handle_time_selection(update, context):
    """Обработчик выбора времени"""
    user_id = update.effective_user.id
    selected_time = update.message.text
    
    if selected_time in SCHEDULE['time_slots']:
        context.user_data['booking_time'] = selected_time
        
        choose_location_text = language_manager.get_text(user_id, 'booking.choose_location')
        reply_markup = get_locations_keyboard(user_id)
        
        await update.message.reply_text(
            choose_location_text,
            reply_markup=reply_markup
        )
        
        return States.BOOKING_LOCATION_CHOICE
    else:
        await update.message.reply_text(
            "❌ Неверное время. Выберите из предложенных вариантов",
            reply_markup=get_times_keyboard()
        )
        return States.BOOKING_TIME

async def handle_location_selection(update, context):
    """Обработчик выбора локации"""
    user_id = update.effective_user.id
    selected_location_text = update.message.text
    
    location_id = None
    user_lang = language_manager.get_user_language(user_id)
    
    for loc_id, loc_data in LOCATIONS.items():
        if loc_data['names'].get(user_lang) == selected_location_text:
            location_id = loc_id
            break
    
    if location_id:
        context.user_data['booking_location'] = location_id
        
        enter_name_text = language_manager.get_text(user_id, 'booking.enter_name')
        reply_markup = get_back_keyboard(user_id)
        
        await update.message.reply_text(
            enter_name_text,
            reply_markup=reply_markup
        )
        
        return States.BOOKING_NAME
    else:
        await update.message.reply_text(
            "❌ Неверная локация. Выберите из предложенных вариантов",
            reply_markup=get_locations_keyboard(user_id)
        )
        return States.BOOKING_LOCATION_CHOICE

async def handle_name_input(update, context):
    """Обработчик ввода имени"""
    user_id = update.effective_user.id
    user_name = update.message.text.strip()
    
    if len(user_name) < 2:
        await update.message.reply_text(
            "❌ Имя слишком короткое. Введите ваше имя:",
            reply_markup=get_back_keyboard(user_id)
        )
        return States.BOOKING_NAME
    
    context.user_data['booking_name'] = user_name
    
    confirmation_text = format_booking_confirmation(user_id, context.user_data)
    reply_markup = get_confirmation_keyboard(user_id)
    
    await update.message.reply_text(
        confirmation_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return States.BOOKING_CONFIRM

def format_booking_confirmation(user_id: int, booking_data: dict) -> str:
    """Форматировать текст подтверждения бронирования"""
    user_lang = language_manager.get_user_language(user_id)
    
    location_name = LOCATIONS[booking_data['booking_location']]['names'].get(user_lang, 'en')
    
    if user_lang == 'ru':
        return f"""📋 **ПОДТВЕРЖДЕНИЕ БРОНИРОВАНИЯ**

👤 Имя: {booking_data['booking_name']}
📅 Дата: {booking_data['booking_date']}
🕐 Время: {booking_data['booking_time']}
📍 Локация: {location_name}

✅ Подтвердить или ❌ Отменить?"""
    elif user_lang == 'ar':
        return f"""📋 **تأكيد الحجز**

👤 الاسم: {booking_data['booking_name']}
📅 التاريخ: {booking_data['booking_date']}
🕐 الوقت: {booking_data['booking_time']}
📍 الموقع: {location_name}

✅ تأكيد أو ❌ إلغاء؟"""
    else:
        return f"""📋 **BOOKING CONFIRMATION**

👤 Name: {booking_data['booking_name']}
📅 Date: {booking_data['booking_date']}
🕐 Time: {booking_data['booking_time']}
📍 Location: {location_name}

✅ Confirm or ❌ Cancel?"""

async def handle_booking_confirmation(update, context):
    """Обработчик подтверждения бронирования"""
    user_id = update.effective_user.id
    user_response = update.message.text
    user_lang = language_manager.get_user_language(user_id)
    
    confirm_keywords = ['confirm', 'подтвердить', 'تأكيد']
    cancel_keywords = ['cancel', 'отменить', 'إلغاء']
    
    if any(keyword in user_response.lower() for keyword in confirm_keywords):
        booking_data = context.user_data
        booking = await booking_service.create_booking(
            user_id=user_id,
            date=booking_data['booking_date'],
            time=booking_data['booking_time'],
            location=booking_data['booking_location'],
            user_name=booking_data['booking_name']
        )
        
        if booking:
            booking_details = format_booking_details(booking, user_lang)
            confirm_text = language_manager.get_text(user_id, 'booking.confirm_booking')
            
            await update.message.reply_text(
                f"🎉 {confirm_text}\\n{booking_details}",
                parse_mode='Markdown',
                reply_markup=get_main_menu(user_id)
            )
            
            context.user_data.clear()
            
            return States.MAIN_MENU
        else:
            error_text = language_manager.get_text(user_id, 'errors.saving_error')
            await update.message.reply_text(
                error_text,
                reply_markup=get_main_menu(user_id)
            )
            return States.MAIN_MENU
            
    elif any(keyword in user_response.lower() for keyword in cancel_keywords):
        cancel_text = "❌ Бронирование отменено" if user_lang == 'ru' else "❌ Booking cancelled"
        await update.message.reply_text(
            cancel_text,
            reply_markup=get_main_menu(user_id)
        )
        return States.MAIN_MENU
    else:
        await update.message.reply_text(
            "❌ Пожалуйста, подтвердите или отмените бронирование",
            reply_markup=get_confirmation_keyboard(user_id)
        )
        return States.BOOKING_CONFIRM

def format_booking_details(booking: dict, language: str) -> str:
    """Форматировать детали бронирования"""
    location_name = LOCATIONS[booking['location']]['names'].get(language, 'en')
    
    if language == 'ru':
        return f"""
📅 **ВАША ЗАПИСЬ:**

👤 Имя: {booking['user_name']}
📅 Дата: {booking['date']}
🕐 Время: {booking['time']}
📍 Локация: {location_name}
🎯 Статус: ✅ Подтверждено

📞 **Абдула свяжется с вами для уточнения деталей**
⏰ Время связи: с 7:00 до 18:00

Сохраните эту информацию! ✨"""
    elif language == 'ar':
        return f"""
📅 **حجزك:**

👤 الاسم: {booking['user_name']}
📅 التاريخ: {booking['date']}
🕐 الوقت: {booking['time']}
📍 الموقع: {location_name}
🎯 الحالة: ✅ مؤكد

📞 **عبدلة سيتصل بك لتوضيح التفاصيل**
⏰ ساعات الاتصال: от 7:00 до 18:00

احتفظ بهذه المعلومات! ✨"""
    else:
        return f"""
📅 **YOUR BOOKING:**

👤 Name: {booking['user_name']}
📅 Date: {booking['date']}
🕐 Time: {booking['time']}
📍 Location: {location_name}
🎯 Status: ✅ Confirmed

📞 **Abdula will contact you to clarify details**
⏰ Contact hours: 7:00 AM to 6:00 PM

Save this information! ✨"""

async def handle_language_selection(update, context):
    """Обработка выбора языка"""
    user_id = update.effective_user.id
    text = update.message.text
    
    language_map = {
        'English 🇺🇸': 'en',
        'Russian 🇷🇺': 'ru', 
        'Arabic 🇦🇪': 'ar'
    }
    
    language_code = language_map.get(text, 'en')
    
    language_manager.set_user_language(user_id, language_code)
    
    user = await database_service.get_user(user_id)
    if user:
        user.language = language_code
        user.language_selected = True
        await database_service.update_user(user)
    
    if language_code == 'ru':
        confirmation = "✅ Язык изменен на русский"
    elif language_code == 'ar':
        confirmation = "✅ تم تغيير اللغة إلى العربية"
    else:
        confirmation = "✅ Language changed to English"
    
    await update.message.reply_text(
        confirmation,
        reply_markup=get_main_menu(user_id)
    )
    
    return States.MAIN_MENU

async def handle_contacts(update, context):
    """Обработчик контактов"""
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
    elif user_lang == 'ar':
        contacts_text = f"""📞 **جهات اتصال عبدلة:**

**الهاتف:** {CONTACTS['phone']}
**Telegram:** {CONTACTS['telegram']}
**Instagram:** {CONTACTS['instagram']}

🕒 **ساعات العمل:**
{CONTACTS['support_hours']}"""
    else:
        contacts_text = f"""📞 **ABDULA'S CONTACTS:**

**Phone:** {CONTACTS['phone']}
**Telegram:** {CONTACTS['telegram']}
**Instagram:** {CONTACTS['instagram']}

🕒 **Working hours:**
{CONTACTS['support_hours']}"""
    
    await update.message.reply_text(
        contacts_text,
        parse_mode='Markdown',
        reply_markup=get_main_menu(user_id)
    )

async def handle_locations(update, context):
    """Обработчик локаций"""
    user_id = update.effective_user.id
    user_lang = language_manager.get_user_language(user_id)
    
    from config.settings import LOCATIONS
    
    locations_text = ""
    for loc_id, loc_data in LOCATIONS.items():
        name = loc_data['names'].get(user_lang, loc_data['names']['en'])
        description = loc_data['description'].get(user_lang, loc_data['description']['en'])
        
        locations_text += f"📍 **{name}**\\n"
        locations_text += f"   - {description}\\n"
        locations_text += f"   - 🕒 {loc_data['best_time']}\\n\\n"
    
    await update.message.reply_text(
        locations_text,
        parse_mode='Markdown',
        reply_markup=get_main_menu(user_id)
    )

async def cancel(update, context):
    """Отмена операции"""
    user_id = update.effective_user.id
    user_lang = language_manager.get_user_language(user_id)
    
    cancel_text = "Операция отменена" if user_lang == 'ru' else "Operation cancelled"
    await update.message.reply_text(
        cancel_text,
        reply_markup=get_main_menu(user_id)
    )
    return ConversationHandler.END

async def error_handler(update, context):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")

def main():
    """Основная функция запуска"""
    logger.info("🚀 Kite Bot Pro с AI-ветровым календарем запускается...")
    
    # Инициализация БД
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(database_service.init_db())
    
    # Создание приложения
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Conversation Handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            States.MAIN_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)
            ],
            States.LANGUAGE_SELECTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_language_selection)
            ],
            States.BOOKING_DATE: [
                CallbackQueryHandler(handle_calendar_callback, pattern="^(calendar_|book_date_|cancel_booking)")
            ],
            States.BOOKING_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_time_selection)
            ],
            States.BOOKING_LOCATION_CHOICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_location_selection)
            ],
            States.BOOKING_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name_input)
            ],
            States.BOOKING_CONFIRM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_booking_confirmation)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    
    logger.info("✅ Бот с AI-ветровым календарем запущен и готов к работе!")
    application.run_polling()

if __name__ == '__main__':
    main()
