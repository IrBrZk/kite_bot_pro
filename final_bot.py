#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# final_wind_bot.py - финальная версия с лотами и статусами
import logging
import os
import re
import requests
import sys
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram import error as telegram_error
from datetime import datetime, timedelta

from config.settings import TELEGRAM_BOT_TOKEN, LOCATIONS, SCHEDULE
from config.constants import States
from config.constants import BookingStatus, SUPPORTED_LANGUAGES
import traceback
from services.language_manager import LanguageManager
from services.database_service import DatabaseService
from services.booking_service import BookingService
from services.level_test_service import LevelTestService
from services.safety_service import safety_service

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Set specific log levels for detailed diagnostics
logging.getLogger('telegram').setLevel(logging.DEBUG)
logging.getLogger('httpx').setLevel(logging.INFO)

# Глобальные сервисы
current_states = {}  # Для отслеживания текущих состояний
language_manager = LanguageManager()
# Локации для занятий
LOCATIONS = {
    'dubai': {
        'names': {
            'ru': 'Kite Beach Dubai',
            'en': 'Kite Beach Dubai', 
            'ar': 'كايت بيتش دبي'
        }
    },
    'abudhabi': {
        'names': {
            'ru': 'Kite Beach Abu Dhabi', 
            'en': 'Kite Beach Abu Dhabi',
            'ar': 'كايت بيتش أبوظبي'
        }
    }
}

# Расписание
SCHEDULE = {
    'time_slots': ['07:00', '08:00', '09:00', '10:00', '11:00', '12:00', 
                   '13:00', '14:00', '15:00', '16:00', '17:00', '18:00']
}

database_service = DatabaseService()
booking_service = BookingService(database_service)
level_test_service = LevelTestService(language_manager)

class FinalWindCalendarService:
    def __init__(self, booking_service):
        self.booking_service = booking_service
        self.openweather_key = os.getenv('OPENWEATHER_KEY')
        
        if not self.openweather_key or self.openweather_key == 'your_api_key_here':
            logger.warning("⚠️ OPENWEATHER_KEY не настроен! Используется демо-режим.")
            self.demo_mode = True
        else:
            self.demo_mode = False
            logger.info("✅ OpenWeather API активирован")
    
    def get_wind_forecast(self, date: str, location: str = "Dubai"):
        """Получить реальный прогноз ветра с OpenWeather"""
        if self.demo_mode:
            import random
            return round(random.uniform(5, 25), 1)
        
        url = "http://api.openweathermap.org/data/2.5/forecast"
        params = {
            "q": location,
            "appid": self.openweather_key,
            "units": "metric",
            "lang": "ru"
        }
        
        try:
            logger.info(f"🌪️ Запрашиваем прогноз для {date} в {location}")
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"OpenWeather API error: {response.status_code} - {response.text}")
                return None
                
            data = response.json()
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
            
            day_forecasts = []
            for item in data.get('list', []):
                forecast_time = datetime.fromtimestamp(item['dt'])
                if (forecast_time.date() == target_date and 
                    8 <= forecast_time.hour <= 20):
                    
                    wind_speed = item['wind']['speed'] * 3.6
                    day_forecasts.append(wind_speed)
            
            if day_forecasts:
                avg_wind = sum(day_forecasts) / len(day_forecasts)
                logger.info(f"📊 Прогноз ветра для {date}: {round(avg_wind, 1)} узлов")
                return round(avg_wind, 1)
            else:
                logger.warning(f"❌ Нет данных прогноза для {date}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка прогноза: {e}")
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
        """Определить качество ветра для кайтсерфинга"""
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
        """Создать клавиатуру календаря с реальным прогнозом ветра"""
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
        
        # Дни месяца с реальным прогнозом ветра
        for week in calendar_data['days']:
            week_buttons = []
            for day_data in week:
                date_str = day_data['date'].strftime("%Y-%m-%d")
                day_num = day_data['date'].day
                
                if not day_data['is_current_month']:
                    week_buttons.append(InlineKeyboardButton(" ", callback_data="ignore"))
                elif day_data['is_past']:
                    week_buttons.append(InlineKeyboardButton(f"❌", callback_data="ignore"))
                else:
                    wind_speed = self.get_wind_forecast(date_str)
                    wind_emoji, wind_quality = self.get_wind_quality(wind_speed)
                    
                    if wind_speed is not None:
                        if wind_quality == "идеальный":
                            label = f"🟢{day_num}🌪"
                        elif wind_quality == "слабый":
                            label = f"🔴{day_num}"
                        elif wind_quality == "сильный":
                            label = f"🔴{day_num}💨"
                        else:
                            label = f"🟡{day_num}"
                    else:
                        label = f"⚪{day_num}"
                    
                    if day_data['is_today']:
                        label = f"📅{day_num}"
                    
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
        
        # Статус API
        status_text = "🌪 Реальный прогноз" if not self.demo_mode else "🎭 Демо-режим"
        keyboard.append([InlineKeyboardButton(status_text, callback_data="ignore")])
        
        # Кнопка домой
        keyboard.append([InlineKeyboardButton("🏠 Домой", callback_data="home")])
        
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
        """Получить детальное описание ветра для выбранной даты"""
        wind_speed = self.get_wind_forecast(date)
        
        if wind_speed is None:
            return "🌐 *Прогноз ветра временно недоступен*\nРекомендуем уточнить условия у Абдулы 📞"
        
        wind_emoji, wind_quality = self.get_wind_quality(wind_speed)
        
        descriptions = {
            "идеальный": f"🎉 *ИДЕАЛЬНЫЙ ДЕНЬ ДЛЯ КАТАНИЯ!*\nВетер {wind_speed} узлов - прекрасные условия! 🌪️",
            "хороший": f"👍 *Хорошие условия*\nВетер {wind_speed} узлов - можно кататься! 💨", 
            "слабый": f"⚠️ *Слабый ветер*\n{wind_speed} узлов - возможно, лучше перенести занятие",
            "сильный": f"🌪️ *СИЛЬНЫЙ ВЕТЕР!*\n{wind_speed} узлов - только для опытных райдеров",
            "нет данных": "🌐 *Данные о ветре отсутствуют*\nУточните условия у инструктора"
        }
        
        return f"{wind_emoji} {descriptions[wind_quality]}"

# Инициализация календаря
calendar_service = FinalWindCalendarService(booking_service)

# ==================== КЛАВИАТУРЫ ====================

def get_main_menu(user_id: int):
    """Упрощенное главное меню"""
    try:
        user_lang = language_manager.get_user_language(user_id)
        logger.debug(f"DBG_GET_MAIN_MENU: Building menu for user {user_id}, language: {user_lang}")
        
        # Простые захардкоженные меню
        if user_lang == 'ru':
            keyboard = [
                ["📅 Бронирование", "📋 Мои брони"],
                ["🎯 Тест уровня", "🛟 Безопасность"],
                ["📍 Локации", "📞 Контакты"],
                ["🌐 Язык", "📸 Галерея"],
                ["🏠 Домой"]
            ]
        elif user_lang == 'ar':
            keyboard = [
                ["📅 الحجز", "📋 حجوزاتي"],
                ["🎯 اختبار المستوى", "🛟 السلامة"],
                ["📍 المواقع", "📞 جهات الاتصال"],
                ["🌐 اللغة", "📸 المعرض"],
                ["🏠 الرئيسية"]
            ]
        else:
            keyboard = [
                ["📅 Booking", "📋 My Bookings"],
                ["🎯 Level Test", "🛟 Safety"],
                ["📍 Locations", "📞 Contacts"],
                ["🌐 Language", "📸 Gallery"],
                ["🏠 Home"]
            ]
        
        logger.debug(f"DBG_GET_MAIN_MENU: Menu built successfully for user {user_id} with language {user_lang}")
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
    except Exception as e:
        logger.error(f"❌ GET_MAIN_MENU ERROR for user {user_id}: {e}", exc_info=True)
        # Ultimate fallback
        keyboard = [["📅 Booking", "📋 My Bookings"], ["🌐 Language"], ["🏠 Home"]]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_times_keyboard():
    times = SCHEDULE['time_slots']
    keyboard = []
    row = []
    for i, time in enumerate(times):
        row.append(time)
        if len(row) == 3 or i == len(times) - 1:
            keyboard.append(row)
            row = []
    keyboard.append(["🏠 Home"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_locations_keyboard(user_id: int):
    user_lang = language_manager.get_user_language(user_id)
    keyboard = []
    for loc_id, loc_data in LOCATIONS.items():
        location_name = loc_data['names'].get(user_lang, loc_data['names']['en'])
        keyboard.append([location_name])
    keyboard.append(["🏠 Home"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_lot_selection_keyboard(selected_lots: list = None):
    """Клавиатура для выбора часов (1-8)"""
    if selected_lots is None:
        selected_lots = []
    
    keyboard = []
    row = []
    
    # Кнопки выбора часов
    for i in range(1, 9):
        hour_text = f"{i} час" + ("ов" if i > 1 else "")
        if i in selected_lots:
            hour_text = f"✅ {hour_text}"
        row.append(hour_text)
        if len(row) == 3:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    if selected_lots:
        keyboard.append(["✅ Подтвердить выбор лотов"])
    
    keyboard.append(["🏠 Home"])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_final_confirmation_keyboard(user_id: int):
    user_lang = language_manager.get_user_language(user_id)
    if user_lang == 'ru':
        confirm_text, cancel_text = "✅ Подтвердить бронирование", "❌ Отменить"
    elif user_lang == 'ar':
        confirm_text, cancel_text = "✅ تأكيد الحجز", "❌ إلغاء"
    else:
        confirm_text, cancel_text = "✅ Confirm Booking", "❌ Cancel"
    
    return ReplyKeyboardMarkup([
        [confirm_text],
        [cancel_text],
        ["🏠 Home"]
    ], resize_keyboard=True)

def get_contact_confirmation_keyboard(user_id: int):
    user_lang = language_manager.get_user_language(user_id)
    if user_lang == 'ru':
        confirm_text, skip_text = "✅ Подтвердить", "⏭ Пропустить"
    elif user_lang == 'ar':
        confirm_text, skip_text = "✅ تأكيد", "⏭ تخطي"
    else:
        confirm_text, skip_text = "✅ Confirm", "⏭ Skip"
    
    return ReplyKeyboardMarkup([
        [confirm_text, skip_text],
        ["🏠 Home"]
    ], resize_keyboard=True)


def get_language_keyboard():
    languages = list(SUPPORTED_LANGUAGES.values())
    keyboard = [
        [languages[0], languages[1]],
        [languages[2]],
        ["🏠 Домой"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_times_keyboard():
    times = SCHEDULE['time_slots']
    keyboard = []
    row = []
    for i, time in enumerate(times):
        row.append(time)
        if len(row) == 3 or i == len(times) - 1:
            keyboard.append(row)
            row = []
    keyboard.append(["🏠 Домой"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)



def get_lot_selection_keyboard(selected_lots: list = None):
    """Клавиатура для выбора нескольких часов"""
    if selected_lots is None:
        selected_lots = []
    
    keyboard = []
    row = []
    
    # Кнопки выбора часов (1-8)
    for i in range(1, 9):
        hour_text = f"{i} час" + ("ов" if i > 1 else "")
        if i in selected_lots:
            hour_text = f"✅ {hour_text}"
        row.append(hour_text)
        if len(row) == 3:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    # Кнопка подтверждения
    if selected_lots:
        keyboard.append(["✅ Подтвердить выбор лотов"])
    
    keyboard.append(["🏠 Домой"])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_locations_keyboard(user_id: int):
    user_lang = language_manager.get_user_language(user_id)
    keyboard = []
    for loc_id, loc_data in LOCATIONS.items():
        location_name = loc_data['names'].get(user_lang, loc_data['names']['en'])
        keyboard.append([location_name])
    keyboard.append(["🏠 Домой"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_lot_selection_keyboard(selected_lots: list = None):
    """Клавиатура для выбора нескольких часов"""
    if selected_lots is None:
        selected_lots = []
    
    keyboard = []
    row = []
    
    # Кнопки выбора часов (1-8)
    for i in range(1, 9):
        hour_text = f"{i} час" + ("ов" if i > 1 else "")
        if i in selected_lots:
            hour_text = f"✅ {hour_text}"
        row.append(hour_text)
        if len(row) == 3:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    # Кнопка подтверждения
    if selected_lots:
        keyboard.append(["✅ Подтвердить выбор лотов"])
    
    keyboard.append(["🏠 Домой"])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_contact_confirmation_keyboard(user_id: int):
    user_lang = language_manager.get_user_language(user_id)
    if user_lang == 'ru':
        confirm_text, skip_text = "✅ Подтвердить", "⏭ Пропустить"
    elif user_lang == 'ar':
        confirm_text, skip_text = "✅ تأكيد", "⏭ تخطي"
    else:
        confirm_text, skip_text = "✅ Confirm", "⏭ Skip"
    
    return ReplyKeyboardMarkup([
        [confirm_text, skip_text],
        ["🏠 Домой"]
    ], resize_keyboard=True)

def get_final_confirmation_keyboard(user_id: int):
    user_lang = language_manager.get_user_language(user_id)
    if user_lang == 'ru':
        confirm_text, cancel_text = "✅ Подтвердить бронирование", "❌ Отменить"
    elif user_lang == 'ar':
        confirm_text, cancel_text = "✅ تأكيد الحجز", "❌ إلغاء"
    else:
        confirm_text, cancel_text = "✅ Confirm Booking", "❌ Cancel"
    
    return ReplyKeyboardMarkup([
        [confirm_text],
        [cancel_text],
        ["🏠 Домой"]
    ], resize_keyboard=True)

# ==================== ОСНОВНЫЕ ОБРАБОТЧИКИ ====================
async def start(update, context):
    user = update.effective_user
    user_id = user.id
    logger.info(f"👋 User: {user_id} - {user.first_name}")

    # Проверяем пользователя в базе и получаем его язык
    user_obj = await database_service.get_user(user_id)
    if not user_obj:
        user_obj = await database_service.create_user(user)
    
    # Устанавливаем язык пользователя в language_manager
    # Сначала проверяем language_manager, потом базу, потом по умолчанию 'en'
    current_lang = language_manager.get_user_language(user_id)
    if current_lang == 'en':  # Если язык не установлен в language_manager
        user_lang = getattr(user_obj, 'language', 'en')
        language_manager.set_user_language(user_id, user_lang)
    else:
        user_lang = current_lang
    
    logger.info(f"🌐 User {user_id} language: {user_lang}")
    
    # Приветствие на языке пользователя
    welcome_text = language_manager.get_text(user_id, 'welcome').format(first_name=user.first_name)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu(user_id),
        parse_mode='Markdown'
    )
    return States.MAIN_MENU

async def handle_main_menu(update, context):
    user_id = update.effective_user.id
    text = update.message.text
    
    # Обновляем текущее состояние
    current_states[user_id] = States.MAIN_MENU
    print(f"🔧 MAIN_MENU: User {user_id} entered main menu, text: '{text}'")
    user_id = update.effective_user.id
    text = update.message.text
    
    logger.info(f"📝 User {user_id} selected: {text}")
    
    # Проверяем кнопку домой на всех языках
    home_buttons = ["🏠 Домой", "🏠 Home", "🏠 الرئيسية"]
    if any(home in text for home in home_buttons):
        await update.message.reply_text("🏠 Главное меню", reply_markup=get_main_menu(user_id))
        return States.MAIN_MENU
    
    if "Бронирование" in text or "Booking" in text or "الحجز" in text:
        return await start_booking(update, context)
    elif "Мои брони" in text or "My Bookings" in text or "حجوزاتي" in text:
        return await show_my_bookings(update, context)
    elif "Тест уровня" in text or "Level Test" in text or "اختبار المستوى" in text:
        return await start_level_test(update, context)
    elif "Безопасность" in text or "Safety" in text or "السلامة" in text:
        return await show_safety_rules(update, context)
    elif "Галерея" in text or "Gallery" in text or "المعرض" in text:
        await update.message.reply_text("📸 Галерея в разработке...", reply_markup=get_main_menu(user_id))
    elif "Язык" in text or "Language" in text or "اللغة" in text:
        await update.message.reply_text("🌐 Выберите язык:", reply_markup=get_language_keyboard())
        return States.LANGUAGE_SELECTION
    elif "Контакты" in text or "Contacts" in text or "جهات الاتصال" in text:
        await handle_contacts(update, context)
    elif "Локации" in text or "Locations" in text or "المواقع" in text:
        await handle_locations(update, context)
    else:
        await update.message.reply_text("❌ Неизвестная команда", reply_markup=get_main_menu(user_id))
    return States.MAIN_MENU

async def handle_lot_selection(update, context):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # Инициализация
    if 'selected_lots' not in context.user_data:
        context.user_data['selected_lots'] = []

    selected_lots = context.user_data['selected_lots']

    # Обработка подтверждения
    confirm_text = language_manager.get_text(user_id, 'booking.confirm_lots')
    if text == confirm_text and selected_lots:
        context.user_data['total_hours'] = sum(selected_lots)
        await update.message.reply_text("Переходим к контактам...")
        return States.BOOKING_CONTACTS

    # Обработка выбора 1–8 часов
    found = False
    for i in range(1, 9):
        hour_ru = f"{i} час" + ("ов" if i > 1 else "")
        hour_en = f"{i} hour" + ("s" if i > 1 else "")
        hour_ar = f"{i} ساعة"

        if hour_ru in text or hour_en in text or hour_ar in text:
            if i in selected_lots:
                selected_lots.remove(i)
                await update.message.reply_text(f"❌ {i} час(ов) удалено")
            else:
                selected_lots.append(i)
                await update.message.reply_text(f"✅ {i} час(ов) добавлено")
            selected_lots.sort()
            found = True
            break

    if not found:
        await update.message.reply_text("Введите число от 1 до 8 (например: 3 часа)")

    # Формируем сообщение
    count = len(selected_lots)
    if count > 0:
        hours_list = ", ".join([f"{h} час{'ов' if h > 1 else ''}" for h in selected_lots])
        message = f"Выбрано: {count} час{'ов' if count > 1 else ''}\nЧасы: {hours_list}\n\nНажмите «{confirm_text}» для продолжения"
    else:
        message = "Выберите количество часов подряд (1–8)\n\nВведите число, например: 3 часа"

    keyboard = get_lot_selection_keyboard(selected_lots)
    await update.message.reply_text(message, reply_markup=keyboard)
    return States.BOOKING_LOT_SELECTION
async def start_booking(update, context):
    user_id = update.effective_user.id
    context.user_data.clear()
    
    status_note = "🌪️ *Реальный прогноз ветра от OpenWeather*" if not calendar_service.demo_mode else "🎭 *Демо-режим*"
    choose_date_text = f"📅 *Выберите дату для занятия*\n\n{status_note}"
    
    keyboard = calendar_service.get_calendar_keyboard()
    await update.message.reply_text(choose_date_text, reply_markup=keyboard, parse_mode='Markdown')
    return States.BOOKING_DATE
    
async def handle_time_selection(update, context):
    user_id = update.effective_user.id
    selected_time = update.message.text
    
    if selected_time == "🏠 Домой":
        await update.message.reply_text("🏠 Главное меню", reply_markup=get_main_menu(user_id))
        return States.MAIN_MENU
    
    if selected_time in SCHEDULE['time_slots']:
        context.user_data['booking_time'] = selected_time
        logger.info(f"BOOKING_TIME: user_id={user_id}, selected_time={selected_time}")
        choose_location_text = "📍 *Выберите локацию для занятия*"
        await update.message.reply_text(choose_location_text, reply_markup=get_locations_keyboard(user_id))
        return States.BOOKING_LOCATION_CHOICE
    else:
        await update.message.reply_text("❌ Неверное время", reply_markup=get_times_keyboard())
        return States.BOOKING_TIME

async def handle_location_selection(update, context):
    user_id = update.effective_user.id
    selected_location_text = update.message.text
    
    if selected_location_text == "🏠 Домой":
        await update.message.reply_text("🏠 Главное меню", reply_markup=get_main_menu(user_id))
        return States.MAIN_MENU
    
    user_lang = language_manager.get_user_language(user_id)
    
    location_id = None
    for loc_id, loc_data in LOCATIONS.items():
        if loc_data['names'].get(user_lang) == selected_location_text:
            location_id = loc_id
            break
    
    if location_id:
        context.user_data['booking_location'] = location_id
        
        lot_selection_text = "🎯 *Выберите количество лотов*\n\n1 лот = 1 час занятия\nМинимум 1 лот, максимум 8 лотов подряд"
        
        await update.message.reply_text(
            lot_selection_text, 
            reply_markup=get_lot_selection_keyboard(),
            parse_mode='Markdown'
        )
        return States.BOOKING_LOT_SELECTION
    else:
        await update.message.reply_text("❌ Неверная локация", reply_markup=get_locations_keyboard(user_id))
        return States.BOOKING_LOCATION_CHOICE

async def handle_lot_selection(update, context):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # Инициализация
    if 'selected_lots' not in context.user_data:
        context.user_data['selected_lots'] = []

    selected_lots = context.user_data['selected_lots']

    # Обработка подтверждения
    confirm_text = language_manager.get_text(user_id, 'booking.confirm_lots')
    if text == confirm_text and selected_lots:
        context.user_data['total_hours'] = sum(selected_lots)
        await update.message.reply_text("Переходим к контактам...")
        return States.BOOKING_CONTACTS

    # Обработка выбора 1–8 часов
    found = False
    for i in range(1, 9):
        hour_ru = f"{i} час" + ("ов" if i > 1 else "")
        hour_en = f"{i} hour" + ("s" if i > 1 else "")
        hour_ar = f"{i} ساعة"

        if hour_ru in text or hour_en in text or hour_ar in text:
            if i in selected_lots:
                selected_lots.remove(i)
                await update.message.reply_text(f"❌ {i} час(ов) удалено")
            else:
                selected_lots.append(i)
                await update.message.reply_text(f"✅ {i} час(ов) добавлено")
            selected_lots.sort()
            found = True
            break

    if not found:
        await update.message.reply_text("Введите число от 1 до 8 (например: 3 часа)")

    # Формируем сообщение
    count = len(selected_lots)
    if count > 0:
        hours_list = ", ".join([f"{h} час{'ов' if h > 1 else ''}" for h in selected_lots])
        message = f"Выбрано: {count} час{'ов' if count > 1 else ''}\nЧасы: {hours_list}\n\nНажмите «{confirm_text}» для продолжения"
    else:
        message = "Выберите количество часов подряд (1–8)\n\nВведите число, например: 3 часа"

    keyboard = get_lot_selection_keyboard(selected_lots)
    await update.message.reply_text(message, reply_markup=keyboard)
    return States.BOOKING_LOT_SELECTION
async def handle_contact_input(update, context):
    user_id = update.effective_user.id
    user_input = update.message.text
    
    if user_input == "🏠 Домой":
        await update.message.reply_text("🏠 Главное меню", reply_markup=get_main_menu(user_id))
        return States.MAIN_MENU
    
    if user_input in ["✅ Подтвердить", "⏭ Пропустить"]:
        if user_input == "⏭ Пропустить":
            context.user_data['user_contacts'] = {
                'name': 'Не указано',
                'phone': 'Не указан', 
                'email': 'Не указан'
            }
        
        confirmation_text = format_booking_confirmation(user_id, context.user_data)
        await update.message.reply_text(
            confirmation_text,
            reply_markup=get_final_confirmation_keyboard(user_id),
            parse_mode='Markdown'
        )
        return States.BOOKING_FINAL_CONFIRM
    else:
        contacts = parse_contact_info(user_input)
        context.user_data['user_contacts'] = contacts
        
        confirmation_text = format_booking_confirmation(user_id, context.user_data)
        await update.message.reply_text(
            confirmation_text,
            reply_markup=get_final_confirmation_keyboard(user_id),
            parse_mode='Markdown'
        )
        return States.BOOKING_FINAL_CONFIRM

def parse_contact_info(text: str) -> dict:
    contacts = {
        'name': 'Не указано',
        'phone': 'Не указан',
        'email': 'Не указан'
    }
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if '@' in line and '.' in line:
            contacts['email'] = line
        elif re.search(r'[\d\s\-\+\(\)]{7,}', line):
            contacts['phone'] = line
        elif contacts['name'] == 'Не указано' and re.match(r'^[а-яА-Яa-zA-Z\s]{2,}$', line):
            contacts['name'] = line
    
    return contacts

async def handle_final_confirmation(update, context):
    user_id = update.effective_user.id
    user_response = update.message.text
    
    if user_response == "🏠 Домой":
        await update.message.reply_text("🏠 Главное меню", reply_markup=get_main_menu(user_id))
        return States.MAIN_MENU
    
    if "✅ Подтвердить бронирование" in user_response or "✅ Confirm Booking" in user_response or "✅ تأكيد الحجز" in user_response:
        booking_data = context.user_data
        
        logger.info(f"BOOKING_SAVE: user_id={user_id}, date={booking_data.get('booking_date')}, time={booking_data.get('booking_time')}, location={booking_data.get('booking_location')}")
        
        successful_bookings = []
        
        for lot_count in booking_data.get('selected_lots', [1]):
            booking = booking_service.create_booking(
                user_id=user_id,
                date=booking_data['booking_date'],
                time=booking_data.get('booking_time', '10:00'),
                location=booking_data['booking_location'],
                user_name=booking_data['user_contacts']['name'],
                lots=lot_count,
                user_phone=booking_data['user_contacts']['phone'],
                user_email=booking_data['user_contacts']['email']
            )
            
            if booking:
                successful_bookings.append(booking)
                logger.info(f"BOOKING_CREATED: booking_id={booking.get('id', 'N/A')}, user_id={user_id}")
        
        if successful_bookings:
            success_text = format_successful_booking(user_id, successful_bookings)
            await update.message.reply_text(success_text, parse_mode='Markdown', reply_markup=get_main_menu(user_id))
        else:
            error_text = "❌ Ошибка при создании бронирования"
            await update.message.reply_text(error_text, reply_markup=get_main_menu(user_id))
        
        context.user_data.clear()
        return States.MAIN_MENU
        
    elif "❌ Отменить" in user_response or "❌ Cancel" in user_response or "❌ إلغاء" in user_response:
        user_lang = language_manager.get_user_language(user_id)
        cancel_text = "❌ Бронирование отменено" if user_lang == 'ru' else "❌ Booking cancelled"
        await update.message.reply_text(cancel_text, reply_markup=get_main_menu(user_id))
        return States.MAIN_MENU
    else:
        await update.message.reply_text("❌ Подтвердите или отмените бронирование", reply_markup=get_final_confirmation_keyboard(user_id))
        return States.BOOKING_FINAL_CONFIRM

def format_booking_confirmation(user_id: int, booking_data: dict) -> str:
    user_lang = language_manager.get_user_language(user_id)
    location_name = LOCATIONS[booking_data['booking_location']]['names'].get(user_lang, 'en')
    
    # Форматируем выбранные лоты (множественный выбор)
    selected_lots = context.user_data.get('selected_lots', [1])
    if selected_lots:
        lots_text = ", ".join([f"{lot} час{'ов' if lot > 1 else ''}" for lot in selected_lots])
        total_hours = sum(selected_lots)
    else:
        lots_text = "1 час"
        total_hours = 1
    selected_lots = booking_data.get('selected_lots', [1])
    if selected_lots:
        lots_text = ", ".join([f"{lot} час{'ов' if lot > 1 else ''}" for lot in selected_lots])
        total_hours = sum(selected_lots)
    else:
        lots_text = "1 час"
        total_hours = 1
    
    if user_lang == 'ru':
        return f"""📋 **ПОДТВЕРЖДЕНИЕ БРОНИРОВАНИЯ**

📅 Дата: {booking_data['booking_date']}
🕐 Время: {booking_data.get('booking_time', 'по договоренности')}
📍 Локация: {location_name}
🎯 Выбрано часов: {lots_text}
⏱️ Общее время: {total_hours} час{'ов' if total_hours > 1 else ''}

**Статус:** {BookingStatus.get_display_name(BookingStatus.BOOKED, user_lang)}

✅ Подтвердить бронирование или ❌ Отменить?"""
    elif user_lang == 'ar':
        return f"""📋 **تأكيد الحجز**

👤 الاسم: {contacts.get('name', 'غير محدد')}
📞 الهاتف: {contacts.get('phone', 'غير محدد')}
📧 البريد: {contacts.get('email', 'غير محدد')}

📅 التاريخ: {booking_data['booking_date']}
🕐 الوقت: {booking_data.get('booking_time', 'بالاتفاق')}
📍 الموقع: {location_name}
🎯 الحصص: {lots_text}

**الحالة:** {BookingStatus.get_display_name(BookingStatus.BOOKED, user_lang)}

✅ تأكيد الحجز أو ❌ إلغاء؟"""
    else:
        return f"""📋 **BOOKING CONFIRMATION**

👤 Name: {contacts.get('name', 'Not specified')}
📞 Phone: {contacts.get('phone', 'Not specified')}
📧 Email: {contacts.get('email', 'Not specified')}

📅 Date: {booking_data['booking_date']}
🕐 Time: {booking_data.get('booking_time', 'by agreement')}
📍 Location: {location_name}
🎯 Lots: {lots_text}

**Status:** {BookingStatus.get_display_name(BookingStatus.BOOKED, user_lang)}

✅ Confirm Booking or ❌ Cancel?"""

def format_successful_booking(user_id: int, bookings: list) -> str:
    user_lang = language_manager.get_user_language(user_id)
    
    if user_lang == 'ru':
        text = f"""🎉 **БРОНИРОВАНИЕ СОЗДАНО!**

✅ Успешно создано {len(bookings)} бронирований:

"""
        for booking in bookings:
            location_name = LOCATIONS[booking['location']]['names'].get(user_lang, 'en')
            text += f"""📅 **Бронирование #{booking.get('id', 'N/A')}**
Дата: {booking['date']}
Лоты: {booking.get('lots', 1)}
Локация: {location_name}
Статус: {BookingStatus.get_display_name(booking.get('status', BookingStatus.BOOKED), user_lang)}

"""
        
        text += "\n📞 *Администратор свяжется с вами для подтверждения*"
        return text
    else:
        text = f"""🎉 **BOOKING CREATED!**

✅ Successfully created {len(bookings)} bookings:

"""
        for booking in bookings:
            location_name = LOCATIONS[booking['location']]['names'].get(user_lang, 'en')
            text += f"""📅 **Booking #{booking.get('id', 'N/A')}**
Date: {booking['date']}
Lots: {booking.get('lots', 1)}
Location: {location_name}
Status: {BookingStatus.get_display_name(booking.get('status', BookingStatus.BOOKED), user_lang)}

"""
        
        text += "\n📞 *Administrator will contact you for confirmation*"
        return text

# ==================== МОИ БРОНИРОВАНИЯ ====================
async def show_my_bookings(update, context):
    user_id = update.effective_user.id
    user_lang = language_manager.get_user_language(user_id)
    
    bookings = booking_service.get_user_bookings(user_id)
    
    if not bookings:
        no_bookings_text = "📭 У вас пока нет бронирований" if user_lang == 'ru' else "📭 You have no bookings yet"
        await update.message.reply_text(no_bookings_text, reply_markup=get_main_menu(user_id))
        return States.MAIN_MENU
    
    if user_lang == 'ru':
        header = "📋 **ВАШИ БРОНИРОВАНИЯ**\n\n"
    else:
        header = "📋 **YOUR BOOKINGS**\n\n"
    
    for booking in bookings:
        if not booking:
            continue
        location_name = LOCATIONS[booking['location']]['names'].get(user_lang, 'en')
        status_display = BookingStatus.get_display_name(booking['status'], user_lang)
        
        if user_lang == 'ru':
            header += f"""📅 **Бронирование #{booking.get('id', 'N/A')}**
Дата: {booking['date']}
Время: {booking['time']}
Лоты: {booking.get('lots', 1)}
Локация: {location_name}
Статус: {status_display}

"""
        else:
            header += f"""📅 **Booking #{booking.get('id', 'N/A')}**
Date: {booking['date']}
Time: {booking['time']}
Lots: {booking.get('lots', 1)}
Location: {location_name}
Status: {status_display}

"""
    
    await update.message.reply_text(header, parse_mode='Markdown', reply_markup=get_main_menu(user_id))
    return States.MAIN_MENU

# ==================== МОДУЛЬ ТЕСТИРОВАНИЯ УРОВНЯ ====================
async def start_level_test(update, context):
    user_id = update.effective_user.id
    level_test_service.start_test(user_id)
    
    question_data = level_test_service.get_question(1, user_id)
    
    keyboard = []
    for i, option in enumerate(question_data['options']):
        keyboard.append([f"{i+1}. {option}"])
    keyboard.append(["🏠 Домой"])
    
    await update.message.reply_text(
        question_data['text'],
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode='Markdown'
    )
    return States.LEVEL_TEST_Q1

async def handle_level_test_answer(update, context, question_num: int, next_state):
    user_id = update.effective_user.id
    answer_text = update.message.text
    
    if answer_text == "🏠 Домой":
        await update.message.reply_text("🏠 Главное меню", reply_markup=get_main_menu(user_id))
        return States.MAIN_MENU
    
    if answer_text.startswith(tuple(str(i) for i in range(1, 5))):
        answer_index = int(answer_text[0]) - 1
        level_test_service.save_answer(user_id, answer_index)
        
        if level_test_service.is_test_completed(user_id):
            level = level_test_service.calculate_level(user_id)
            level_description = level_test_service.get_level_description(level, user_id)
            
            await update.message.reply_text(
                level_description,
                reply_markup=get_main_menu(user_id),
                parse_mode='Markdown'
            )
            
            database_service.update_user_level(user_id, level)
            return States.MAIN_MENU
        else:
            next_question_num = level_test_service.get_current_question(user_id)
            question_data = level_test_service.get_question(next_question_num, user_id)
            
            keyboard = []
            for i, option in enumerate(question_data['options']):
                keyboard.append([f"{i+1}. {option}"])
            keyboard.append(["🏠 Домой"])
            
            await update.message.reply_text(
                question_data['text'],
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
                parse_mode='Markdown'
            )
            return next_state
    else:
        await update.message.reply_text("❌ Пожалуйста, выберите вариант ответа")
        return None

async def handle_level_test_q1(update, context):
    return await handle_level_test_answer(update, context, 1, States.LEVEL_TEST_Q2)

async def handle_level_test_q2(update, context):
    return await handle_level_test_answer(update, context, 2, States.LEVEL_TEST_Q3)

async def handle_level_test_q3(update, context):
    return await handle_level_test_answer(update, context, 3, States.LEVEL_TEST_Q4)

async def handle_level_test_q4(update, context):
    return await handle_level_test_answer(update, context, 4, States.LEVEL_TEST_Q5)

async def handle_level_test_q5(update, context):
    return await handle_level_test_answer(update, context, 5, States.MAIN_MENU)

# ==================== МОДУЛЬ БЕЗОПАСНОСТИ ====================
async def show_safety_rules(update, context):
    user_id = update.effective_user.id
    safety_text = safety_service.get_safety_rules(user_id)
    
    await update.message.reply_text(
        safety_text,
        reply_markup=get_main_menu(user_id),
        parse_mode='Markdown'
    )
    return States.MAIN_MENU

# ==================== ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ====================
async def handle_language_selection(update, context):
    user_id = update.effective_user.id
    selected_language = update.message.text
    
    logger.info(f"DBG_LANG_HANDLER: User {user_id} selected: '{selected_language}'")
    logger.debug(f"DBG_LANG_HANDLER: Current state: {current_states.get(user_id, 'unknown')}")
    
    # Определяем язык
    language_code = 'en'
    success_text = "✅ Language changed to English"
    
    if "Russian" in selected_language or "Русский" in selected_language:
        language_code = 'ru'
        success_text = "✅ Язык изменен на русский"
    elif "Arabic" in selected_language or "العربية" in selected_language:
        language_code = 'ar'
        success_text = "✅ تم تغيير اللغة إلى العربية"
    
    logger.info(f"DBG_LANG_HANDLER: Setting language to: {language_code} for user {user_id}")
    
    # Сохраняем язык в memory manager
    language_manager.set_user_language(user_id, language_code)
    
    # Сохраняем язык в базу данных с обработкой ошибок
    try:
        await database_service.update_user(user_id, language=language_code, language_selected=True)
        logger.debug(f"DBG_LANG_HANDLER: Database updated for user {user_id}")
    except Exception as db_error:
        logger.error(f"❌ Failed to save language to database for user {user_id}: {db_error}", exc_info=True)
        # Continue anyway - language is saved in memory manager
    
    # Сохраняем в context для резервирования
    context.user_data['language'] = language_code
    
    # Обновляем состояние
    current_states[user_id] = States.MAIN_MENU
    
    # Показываем успешное сообщение и главное меню
    try:
        menu = get_main_menu(user_id)
        await update.message.reply_text(success_text, reply_markup=menu)
        logger.info(f"DBG_LANG_HANDLER: Successfully set menu for language: {language_code}, user: {user_id}")
        
        # ВАЖНО: Возвращаем правильное состояние
        return States.MAIN_MENU
        
    except Exception as e:
        logger.error(f"❌ Error in language selection: {e}", exc_info=True)
        # Fallback
        await update.message.reply_text("Language changed!", reply_markup=get_main_menu(user_id))
        return States.MAIN_MENU
    
    language_code = None
    for code, name in SUPPORTED_LANGUAGES.items():
        if name == selected_language:
            language_code = code
            break
    
    if language_code:
        # Сохраняем язык в базе данных
        await database_service.set_user_language(user_id, language_code)
        language_manager.set_user_language(user_id, language_code)
        
        # Получаем текст на выбранном языке
        if language_code == 'ru':
            success_text = "✅ Язык изменен на русский"
        elif language_code == 'ar':
            success_text = "✅ تم تغيير اللغة إلى العربية"
        else:
            success_text = "✅ Language changed to English"
        
        await update.message.reply_text(success_text, reply_markup=get_main_menu(user_id))
        return States.MAIN_MENU
    else:
        await update.message.reply_text("❌ Неверный выбор языка", reply_markup=get_language_keyboard())
        return States.LANGUAGE_SELECTION
async def handle_contacts(update, context):
    user_id = update.effective_user.id
    user_lang = language_manager.get_user_language(user_id)
    
    if user_lang == 'ru':
        contacts_text = """📞 **КОНТАКТЫ АБДУЛЫ:**

**Телефон:** +971 564327509
**Telegram:** @abdula_kite_pro  
**Instagram:** @abdula_kite_dubai

🕒 **Часы работы:**
Ежедневно с 7:00 до 18:00"""
    else:
        contacts_text = """📞 **ABDULA'S CONTACTS:**

**Phone:** +971 564327509
**Telegram:** @abdula_kite_pro
**Instagram:** @abdula_kite_dubai

🕒 **Working hours:**
Daily from 7:00 to 18:00"""
    
    await update.message.reply_text(contacts_text, parse_mode='Markdown', reply_markup=get_main_menu(user_id))
    return States.MAIN_MENU

async def handle_locations(update, context):
    user_id = update.effective_user.id
    user_lang = language_manager.get_user_language(user_id)
    
    locations_text = "📍 **ЛОКАЦИИ ДЛЯ ЗАНЯТИЙ**\n\n" if user_lang == 'ru' else "📍 **LESSON LOCATIONS**\n\n"
    
    for loc_id, loc_data in LOCATIONS.items():
        name = loc_data['names'].get(user_lang, loc_data['names']['en'])
        description = loc_data['description'].get(user_lang, loc_data['description']['en'])
        locations_text += f"**{name}**\n{description}\n🕒 {loc_data['best_time']}\n\n"
    
    await update.message.reply_text(locations_text, parse_mode='Markdown', reply_markup=get_main_menu(user_id))
    return States.MAIN_MENU

async def cancel(update, context):
    user_id = update.effective_user.id
    await update.message.reply_text("Операция отменена", reply_markup=get_main_menu(user_id))
    return States.MAIN_MENU

async def debug_message_handler(update, context):
    """Lightweight debug handler for all messages"""
    if update.effective_user and update.message:
        logger.debug(f"DEBUG_MSG: user_id={update.effective_user.id}, chat_id={update.effective_chat.id}, text='{update.message.text}'")

async def debug_callback_handler(update, context):
    """Lightweight debug handler for all callback queries"""
    if update.effective_user and update.callback_query:
        logger.debug(f"DEBUG_CB: user_id={update.effective_user.id}, chat_id={update.effective_chat.id}, data='{update.callback_query.data}'")

async def unknown_command(update, context):
    """Handle unknown commands gracefully"""
    user_id = update.effective_user.id
    await update.message.reply_text("❌ Неизвестная команда", reply_markup=get_main_menu(user_id))
    return States.MAIN_MENU

async def error_handler(update, context):
    logger.error(f"Ошибка: {context.error}", exc_info=context.error)
    
    if update and update.effective_user:
        user_id = update.effective_user.id
        error_text = "❌ Произошла ошибка. Попробуйте еще раз."
        await update.message.reply_text(error_text, reply_markup=get_main_menu(user_id))
    
    return States.MAIN_MENU

async def handle_calendar(update, context):
    query = update.callback_query
    await query.answer()
    _, year, month = query.data.split("_")
    keyboard = calendar_service.get_calendar_keyboard(int(year), int(month))
    await query.edit_message_reply_markup(reply_markup=keyboard)
    return States.BOOKING_DATE

async def handle_date_select(update, context):
    query = update.callback_query
    await query.answer()
    date = query.data.split("_", 1)[1]
    context.user_data["date"] = date
    await query.message.reply_text(f"Выбрана дата: {date}\nВыберите время:")
    return States.BOOKING_TIME

async def handle_calendar_callback(update, context):
    """Handle calendar navigation and date selection"""
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id

    if data.startswith('calendar_'):
        # Navigate calendar months
        year, month = map(int, data.split('_')[1:])
        keyboard = calendar_service.get_calendar_keyboard(year, month)
        await query.edit_message_reply_markup(reply_markup=keyboard)
        return States.BOOKING_DATE

    elif data.startswith('book_date_'):
        # Select a specific date
        date = data.split('_')[2]
        context.user_data['booking_date'] = date
        logger.info(f"BOOKING_DATE: user_id={user_id}, selected_date={date}")
        await query.message.reply_text(f"Выбрана дата: {date}\nВыберите время:", reply_markup=get_times_keyboard())
        return States.BOOKING_TIME
    
    elif data == 'home':
        # Return to main menu
        await query.message.reply_text("🏠 Главное меню", reply_markup=get_main_menu(user_id))
        return States.MAIN_MENU
    
    # Ignore other callbacks
    return States.BOOKING_DATE

def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN не найден!")
        return
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Debug handlers at group 0 (run first, don't interfere with flow)
    application.add_handler(MessageHandler(filters.ALL, debug_message_handler), group=0)
    application.add_handler(CallbackQueryHandler(debug_callback_handler), group=0)
    
    # Обработчик начала
    application.add_handler(CommandHandler("start", start))
    
    # Unknown command handler
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    
    # Основной ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)],
        states={
            States.MAIN_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)
            ],
            States.LANGUAGE_SELECTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_language_selection)
            ],
            States.BOOKING_DATE: [
                CallbackQueryHandler(handle_calendar_callback, pattern='^(calendar_|book_date_|home|ignore)'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)
            ],
            States.BOOKING_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_time_selection)
            ],
            States.BOOKING_LOCATION_CHOICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_location_selection)
            ],
            States.BOOKING_LOT_SELECTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_lot_selection)
            ],
            States.BOOKING_CONTACTS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_contact_input)
            ],
            States.BOOKING_FINAL_CONFIRM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_final_confirmation)
            ],
            States.LEVEL_TEST_Q1: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_level_test_q1)
            ],
            States.LEVEL_TEST_Q2: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_level_test_q2)
            ],
            States.LEVEL_TEST_Q3: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_level_test_q3)
            ],
            States.LEVEL_TEST_Q4: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_level_test_q4)
            ],
            States.LEVEL_TEST_Q5: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_level_test_q5)
            ]
        },
        fallbacks=[
            CommandHandler("start", start),
            MessageHandler(filters.TEXT & filters.Regex('^🏠'), handle_main_menu),
            CommandHandler("cancel", cancel)
        ],
        allow_reentry=True,
        per_message=True
    )
    
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    
    logger.info("🚀 Финальный бот запущен с новой логикой бронирования!")
    
    # Wrap run_polling to catch Conflict and other errors
    try:
        application.run_polling()
    except telegram_error.Conflict as e:
        logger.error(f"❌ telegram.error.Conflict: {e}. Another instance of the bot is already running. Exiting.", exc_info=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unhandled exception in bot: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()


