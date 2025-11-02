#!/usr/bin/env python3
# fixed_wind_bot.py - бот с исправленным календарем и новой логикой бронирования
import logging
import os
import re
import requests
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

from config.settings import TELEGRAM_BOT_TOKEN, LOCATIONS, SCHEDULE, LOT_DURATION
from config.constants import States, BookingStatus
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

class FixedWindCalendarService:
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
            # Демо-режим: случайный ветер
            import random
            return round(random.uniform(5, 25), 1)
        
        # РЕАЛЬНЫЙ ПРОГНОЗ
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
            
            # Ищем прогнозы на нужную дату в дневное время (10:00-18:00)
            day_forecasts = []
            for item in data.get('list', []):
                forecast_time = datetime.fromtimestamp(item['dt'])
                if (forecast_time.date() == target_date and 
                    8 <= forecast_time.hour <= 20):
                    
                    wind_speed = item['wind']['speed'] * 3.6  # м/с → узлы
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
                    # Реальный прогноз ветра
                    wind_speed = self.get_wind_forecast(date_str)
                    wind_emoji, wind_quality = self.get_wind_quality(wind_speed)
                    
                    # Создаем индикатор с учетом наличия данных
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
                        label = f"⚪{day_num}"  # Нет данных
                    
                    # Подсветка сегодняшнего дня
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

# Инициализация календаря с реальным прогнозом
calendar_service = FixedWindCalendarService(booking_service)

def get_main_menu(user_id: int):
    texts = language_manager.get_all_menu_texts(user_id)
    keyboard = [
        [texts['booking'], texts['my_bookings']],
        [texts['level_test'], texts['safety']],
        [texts['locations'], texts['contacts']],
        [texts['language'], texts['gallery']]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_home_keyboard(user_id: int):
    home_text = language_manager.get_text(user_id, 'menu.home')
    return ReplyKeyboardMarkup([[home_text]], resize_keyboard=True)

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
    home_text = language_manager.get_text(user_id, 'menu.home')
    return ReplyKeyboardMarkup([[back_text], [home_text]], resize_keyboard=True)

def get_times_keyboard(date: str):
    """Клавиатура выбора времени с учетом доступных лотов"""
    times = SCHEDULE['time_slots']
    keyboard = []
    row = []
    for i, time in enumerate(times):
        row.append(time)
        if len(row) == 3 or i == len(times) - 1:
            keyboard.append(row)
            row = []
    
    # Добавляем кнопку "Выбрать все доступные"
    keyboard.append(["✅ Выбрать все доступные"])
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
    """Клавиатура для выбора количества лотов"""
    if selected_lots is None:
        selected_lots = []
    
    keyboard = []
    row = []
    
    # Кнопки выбора количества лотов (от 1 до 8)
    for i in range(1, 9):
        lot_text = f"{i} лот" + ("ов" if i > 1 else "")
        if i in selected_lots:
            lot_text = f"✅ {lot_text}"
        row.append(lot_text)
        if len(row) == 3:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    # Кнопки действий
    if selected_lots:
        keyboard.append(["✅ Подтвердить выбор лотов"])
    
    keyboard.append(["🏠 Домой"])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_contact_confirmation_keyboard(user_id: int):
    user_lang = language_manager.get_user_language(user_id)
    if user_lang == 'ru':
        confirm_text, skip_text, home_text = "✅ Подтвердить", "⏭ Пропустить", "🏠 Домой"
    elif user_lang == 'ar':
        confirm_text, skip_text, home_text = "✅ تأكيد", "⏭ تخطي", "🏠 الرئيسية"
    else:
        confirm_text, skip_text, home_text = "✅ Confirm", "⏭ Skip", "🏠 Home"
    
    return ReplyKeyboardMarkup([
        [confirm_text, skip_text],
        [home_text]
    ], resize_keyboard=True)

def get_final_confirmation_keyboard(user_id: int):
    user_lang = language_manager.get_user_language(user_id)
    if user_lang == 'ru':
        confirm_text, cancel_text, home_text = "✅ Подтвердить бронирование", "❌ Отменить", "🏠 Домой"
    elif user_lang == 'ar':
        confirm_text, cancel_text, home_text = "✅ تأكيد الحجز", "❌ إلغاء", "🏠 الرئيسية"
    else:
        confirm_text, cancel_text, home_text = "✅ Confirm Booking", "❌ Cancel", "🏠 Home"
    
    return ReplyKeyboardMarkup([
        [confirm_text],
        [cancel_text, home_text]
    ], resize_keyboard=True)

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
    elif text == menu_texts['my_bookings']:
        return await show_my_bookings(update, context)
    elif text == menu_texts['level_test']:
        return await start_level_test(update, context)
    elif text == menu_texts['safety']:
        return await show_safety_rules(update, context)
    elif text == menu_texts['gallery']:
        await update.message.reply_text("📸 Галерея в разработке...", reply_markup=get_main_menu(user_id))
    elif text == menu_texts['language']:
        await update.message.reply_text("🌐 Выберите язык:", reply_markup=get_language_keyboard())
        return States.LANGUAGE_SELECTION
    elif text == menu_texts['contacts']:
        await handle_contacts(update, context)
    elif text == menu_texts['locations']:
        await handle_locations(update, context)
    elif text == "🏠 Домой":
        await update.message.reply_text("🏠 Возврат в главное меню", reply_markup=get_main_menu(user_id))
        return States.MAIN_MENU
    else:
        await update.message.reply_text("❌ Неизвестная команда", reply_markup=get_main_menu(user_id))
    return States.MAIN_MENU

async def start_booking(update, context):
    user_id = update.effective_user.id
    context.user_data.clear()
    
    status_note = "🌪️ *Реальный прогноз ветра от OpenWeather*" if not calendar_service.demo_mode else "🎭 *Демо-режим (случайные значения)*"
    choose_date_text = f"{language_manager.get_text(user_id, 'booking.choose_date')}\\n\\n{status_note}"
    
    keyboard = calendar_service.get_calendar_keyboard()
    await update.message.reply_text(choose_date_text, reply_markup=keyboard, parse_mode='Markdown')
    return States.BOOKING_DATE

async def handle_calendar_callback(update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    logger.info(f"📅 Calendar callback: {data} from user {user_id}")
    
    if data == 'home':
        await query.edit_message_text("🏠 Возврат в главное меню")
        await query.message.reply_text("Выберите действие:", reply_markup=get_main_menu(user_id))
        return States.MAIN_MENU
    
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
        if calendar_service.is_date_available(date):
            context.user_data['booking_date'] = date
            wind_description = calendar_service.get_wind_description(date)
            choose_time_text = f"{language_manager.get_text(user_id, 'booking.choose_time')}\\n\\n{wind_description}"
            
            # Проверяем доступные времена для выбранной даты
            available_times = await booking_service.get_available_times(date)
            
            await query.message.reply_text(
                choose_time_text,
                reply_markup=get_times_keyboard(date),
                parse_mode='Markdown'
            )
            return States.BOOKING_TIME
        else:
            await query.answer("❌ Эта дата недоступна", show_alert=True)

async def handle_time_selection(update, context):
    user_id = update.effective_user.id
    selected_time = update.message.text
    
    if selected_time == "🏠 Домой":
        await update.message.reply_text("🏠 Возврат в главное меню", reply_markup=get_main_menu(user_id))
        return States.MAIN_MENU
    
    if selected_time == "✅ Выбрать все доступные":
        # Логика выбора всех доступных времен
        date = context.user_data.get('booking_date')
        available_times = await booking_service.get_available_times(date)
        context.user_data['selected_times'] = available_times
        context.user_data['all_times_selected'] = True
    elif selected_time in SCHEDULE['time_slots']:
        if 'selected_times' not in context.user_data:
            context.user_data['selected_times'] = []
        
        if selected_time in context.user_data['selected_times']:
            context.user_data['selected_times'].remove(selected_time)
            await update.message.reply_text(f"❌ Время {selected_time} удалено из выбора")
        else:
            context.user_data['selected_times'].append(selected_time)
            await update.message.reply_text(f"✅ Время {selected_time} добавлено к выбору")
        
        # Показываем клавиатуру снова для продолжения выбора
        if len(context.user_data['selected_times']) > 0:
            choose_more_text = f"✅ Выбрано времен: {len(context.user_data['selected_times'])}\nВыберите еще время или нажмите '✅ Выбрать все доступные'"
            await update.message.reply_text(choose_more_text, reply_markup=get_times_keyboard(context.user_data['booking_date']))
            return States.BOOKING_TIME
    
    # Переходим к выбору локации если есть выбранные времена
    if context.user_data.get('selected_times') or context.user_data.get('all_times_selected'):
        choose_location_text = language_manager.get_text(user_id, 'booking.choose_location')
        await update.message.reply_text(choose_location_text, reply_markup=get_locations_keyboard(user_id))
        return States.BOOKING_LOCATION_CHOICE
    else:
        await update.message.reply_text("❌ Выберите хотя бы один временной слот", reply_markup=get_times_keyboard(context.user_data['booking_date']))
        return States.BOOKING_TIME

async def handle_location_selection(update, context):
    user_id = update.effective_user.id
    selected_location_text = update.message.text
    
    if selected_location_text == "🏠 Домой":
        await update.message.reply_text("🏠 Возврат в главное меню", reply_markup=get_main_menu(user_id))
        return States.MAIN_MENU
    
    user_lang = language_manager.get_user_language(user_id)
    
    location_id = None
    for loc_id, loc_data in LOCATIONS.items():
        if loc_data['names'].get(user_lang) == selected_location_text:
            location_id = loc_id
            break
    
    if location_id:
        context.user_data['booking_location'] = location_id
        
        # Переходим к выбору количества лотов
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
    selected_text = update.message.text
    
    if selected_text == "🏠 Домой":
        await update.message.reply_text("🏠 Возврат в главное меню", reply_markup=get_main_menu(user_id))
        return States.MAIN_MENU
    
    if selected_text == "✅ Подтвердить выбор лотов":
        if context.user_data.get('selected_lots'):
            # Переходим к вводу контактных данных
            contact_text = "📞 *Контактные данные*\n\nВведите ваши данные в формате:\n• Имя\n• Телефон\n• Email\n\nИли нажмите '⏭ Пропустить' чтобы продолжить без контактов"
            
            await update.message.reply_text(
                contact_text,
                reply_markup=get_contact_confirmation_keyboard(user_id),
                parse_mode='Markdown'
            )
            return States.BOOKING_CONTACTS
        else:
            await update.message.reply_text("❌ Выберите хотя бы один лот", reply_markup=get_lot_selection_keyboard())
            return States.BOOKING_LOT_SELECTION
    
    # Обработка выбора количества лотов
    if 'selected_lots' not in context.user_data:
        context.user_data['selected_lots'] = []
    
    # Парсим количество лотов из текста
    lot_match = re.search(r'(\d+)\s*лот', selected_text)
    if lot_match:
        lot_count = int(lot_match.group(1))
        
        if lot_count in context.user_data['selected_lots']:
            context.user_data['selected_lots'].remove(lot_count)
            await update.message.reply_text(f"❌ {lot_count} лот(ов) удалено из выбора")
        else:
            if lot_count >= 1 and lot_count <= 8:
                context.user_data['selected_lots'].append(lot_count)
                await update.message.reply_text(f"✅ {lot_count} лот(ов) добавлено к выбору")
            else:
                await update.message.reply_text("❌ Можно выбрать от 1 до 8 лотов")
    
    # Показываем обновленную клавиатуру
    await update.message.reply_text(
        f"✅ Выбрано вариантов: {len(context.user_data['selected_lots'])}\nНажмите '✅ Подтвердить выбор лотов' когда закончите",
        reply_markup=get_lot_selection_keyboard(context.user_data['selected_lots'])
    )
    return States.BOOKING_LOT_SELECTION

async def handle_contact_input(update, context):
    user_id = update.effective_user.id
    user_input = update.message.text
    
    if user_input == "🏠 Домой":
        await update.message.reply_text("🏠 Возврат в главное меню", reply_markup=get_main_menu(user_id))
        return States.MAIN_MENU
    
    if user_input in ["✅ Подтвердить", "⏭ Пропустить"]:
        if user_input == "⏭ Пропустить":
            context.user_data['user_contacts'] = {
                'name': 'Не указано',
                'phone': 'Не указан', 
                'email': 'Не указан'
            }
        
        # Переходим к финальному подтверждению
        confirmation_text = format_booking_confirmation(user_id, context.user_data)
        await update.message.reply_text(
            confirmation_text,
            reply_markup=get_final_confirmation_keyboard(user_id),
            parse_mode='Markdown'
        )
        return States.BOOKING_FINAL_CONFIRM
    else:
        # Парсим контактные данные
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
    """Парсит контактные данные из текста"""
    contacts = {
        'name': 'Не указано',
        'phone': 'Не указан',
        'email': 'Не указан'
    }
    
    # Простой парсинг - в реальном боте можно сделать более сложную логику
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Проверяем email
        if '@' in line and '.' in line:
            contacts['email'] = line
        # Проверяем телефон
        elif re.search(r'[\d\s\-\+\(\)]{7,}', line):
            contacts['phone'] = line
        # Считаем именем первую непустую строку без специальных символов
        elif contacts['name'] == 'Не указано' and re.match(r'^[а-яА-Яa-zA-Z\s]{2,}$', line):
            contacts['name'] = line
    
    return contacts

async def handle_final_confirmation(update, context):
    user_id = update.effective_user.id
    user_response = update.message.text
    user_lang = language_manager.get_user_language(user_id)
    
    if user_response == "🏠 Домой":
        await update.message.reply_text("🏠 Возврат в главное меню", reply_markup=get_main_menu(user_id))
        return States.MAIN_MENU
    
    if "✅ Подтвердить бронирование" in user_response:
        # Создаем бронирования для каждого лота
        booking_data = context.user_data
        
        successful_bookings = []
        failed_bookings = []
        
        # Создаем отдельное бронирование для каждого лота
        for lot_count in booking_data.get('selected_lots', [1]):
            booking = await booking_service.create_booking(
                user_id=user_id,
                date=booking_data['booking_date'],
                times=booking_data.get('selected_times', []),
                all_times=booking_data.get('all_times_selected', False),
                location=booking_data['booking_location'],
                lots=lot_count,
                user_name=booking_data['user_contacts']['name'],
                user_phone=booking_data['user_contacts']['phone'],
                user_email=booking_data['user_contacts']['email']
            )
            
            if booking:
                successful_bookings.append(booking)
            else:
                failed_bookings.append(lot_count)
        
        if successful_bookings:
            success_text = format_successful_booking(user_id, successful_bookings)
            await update.message.reply_text(success_text, parse_mode='Markdown', reply_markup=get_main_menu(user_id))
            
            if failed_bookings:
                await update.message.reply_text(f"❌ Не удалось создать брони для {len(failed_bookings)} лотов")
        else:
            error_text = language_manager.get_text(user_id, 'errors.saving_error')
            await update.message.reply_text(error_text, reply_markup=get_main_menu(user_id))
        
        context.user_data.clear()
        return States.MAIN_MENU
        
    elif "❌ Отменить" in user_response:
        cancel_text = "❌ Бронирование отменено" if user_lang == 'ru' else "❌ Booking cancelled"
        await update.message.reply_text(cancel_text, reply_markup=get_main_menu(user_id))
        return States.MAIN_MENU
    else:
        await update.message.reply_text("❌ Подтвердите или отмените бронирование", reply_markup=get_final_confirmation_keyboard(user_id))
        return States.BOOKING_FINAL_CONFIRM

def format_booking_confirmation(user_id: int, booking_data: dict) -> str:
    user_lang = language_manager.get_user_language(user_id)
    location_name = LOCATIONS[booking_data['booking_location']]['names'].get(user_lang, 'en')
    contacts = booking_data.get('user_contacts', {})
    
    # Форматируем выбранные времена
    times_text = ""
    if booking_data.get('all_times_selected'):
        times_text = "Все доступные времена"
    else:
        times_text = ", ".join(booking_data.get('selected_times', []))
    
    # Форматируем выбранные лоты
    lots_text = ", ".join([f"{lot} лот{'ов' if lot > 1 else ''}" for lot in booking_data.get('selected_lots', [])])
    
    if user_lang == 'ru':
        return f"""📋 **ПОДТВЕРЖДЕНИЕ БРОНИРОВАНИЯ**

👤 Имя: {contacts.get('name', 'Не указано')}
📞 Телефон: {contacts.get('phone', 'Не указан')}
📧 Email: {contacts.get('email', 'Не указан')}

📅 Дата: {booking_data['booking_date']}
🕐 Время: {times_text}
📍 Локация: {location_name}
🎯 Лоты: {lots_text}

**Статус:** 🟡 Ожидает подтверждения администратором

✅ Подтвердить бронирование или ❌ Отменить?"""
    elif user_lang == 'ar':
        return f"""📋 **تأكيد الحجز**

👤 الاسم: {contacts.get('name', 'غير محدد')}
📞 الهاتف: {contacts.get('phone', 'غير محدد')}
📧 البريد: {contacts.get('email', 'غير محدد')}

📅 التاريخ: {booking_data['booking_date']}
🕐 الوقت: {times_text}
📍 الموقع: {location_name}
🎯 الحصص: {lots_text}

**الحالة:** 🟡 في انتظار تأكيد المسؤول

✅ تأكيد الحجز أو ❌ إلغاء؟"""
    else:
        return f"""📋 **BOOKING CONFIRMATION**

👤 Name: {contacts.get('name', 'Not specified')}
📞 Phone: {contacts.get('phone', 'Not specified')}
📧 Email: {contacts.get('email', 'Not specified')}

📅 Date: {booking_data['booking_date']}
🕐 Time: {times_text}
📍 Location: {location_name}
🎯 Lots: {lots_text}

**Status:** 🟡 Waiting for admin confirmation

✅ Confirm Booking or ❌ Cancel?"""

def format_successful_booking(user_id: int, bookings: list) -> str:
    user_lang = language_manager.get_user_language(user_id)
    
    if user_lang == 'ru':
        text = f"""🎉 **БРОНИРОВАНИЕ СОЗДАНО!**

✅ Успешно создано {len(bookings)} бронирований:

"""
        for booking in bookings:
            location_name = LOCATIONS[booking.location]['names'].get(user_lang, 'en')
            text += f"""📅 **Бронирование #{booking.id}**
Дата: {booking.date}
Лоты: {booking.lots_count}
Локация: {location_name}
Статус: {BookingStatus.get_display_name(booking.status, user_lang)}

"""
        
        text += "\n📞 *Администратор свяжется с вами для подтверждения*"
        return text
    elif user_lang == 'ar':
        text = f"""🎉 **تم إنشاء الحجز!**

✅ تم إنشاء {len(bookings)} حجز بنجاح:

"""
        for booking in bookings:
            location_name = LOCATIONS[booking.location]['names'].get(user_lang, 'en')
            text += f"""📅 **الحجز #{booking.id}**
التاريخ: {booking.date}
الحصص: {booking.lots_count}
الموقع: {location_name}
الحالة: {BookingStatus.get_display_name(booking.status, user_lang)}

"""
        
        text += "\n📞 *سيتصل بك المسؤول للتأكيد*"
        return text
    else:
        text = f"""🎉 **BOOKING CREATED!**

✅ Successfully created {len(bookings)} bookings:

"""
        for booking in bookings:
            location_name = LOCATIONS[booking.location]['names'].get(user_lang, 'en')
            text += f"""📅 **Booking #{booking.id}**
Date: {booking.date}
Lots: {booking.lots_count}
Location: {location_name}
Status: {BookingStatus.get_display_name(booking.status, user_lang)}

"""
        
        text += "\n📞 *Administrator will contact you for confirmation*"
        return text

async def show_my_bookings(update, context):
    user_id = update.effective_user.id
    user_lang = language_manager.get_user_language(user_id)
    
    bookings = await database_service.get_user_bookings(user_id)
    
    if not bookings:
        no_bookings_text = language_manager.get_text(user_id, 'bookings.none')
        await update.message.reply_text(no_bookings_text, reply_markup=get_main_menu(user_id))
        return States.MAIN_MENU
    
    if user_lang == 'ru':
        header = "📋 **ВАШИ БРОНИРОВАНИЯ**\n\n"
    elif user_lang == 'ar':
        header = "📋 **حجوزاتك**\n\n"
    else:
        header = "📋 **YOUR BOOKINGS**\n\n"
    
    for booking in bookings:
        location_name = LOCATIONS[booking.location]['names'].get(user_lang, 'en')
        status_display = BookingStatus.get_display_name(booking.status, user_lang)
        
        if user_lang == 'ru':
            header += f"""📅 **Бронирование #{booking.id}**
Дата: {booking.date}
Лоты: {booking.lots_count}
Локация: {location_name}
Статус: {status_display}
"""
        elif user_lang == 'ar':
            header += f"""📅 **الحجز #{booking.id}**
التاريخ: {booking.date}
الحصص: {booking.lots_count}
الموقع: {location_name}
الحالة: {status_display}
"""
        else:
            header += f"""📅 **Booking #{booking.id}**
Date: {booking.date}
Lots: {booking.lots_count}
Location: {location_name}
Status: {status_display}
"""
    
    await update.message.reply_text(header, parse_mode='Markdown', reply_markup=get_main_menu(user_id))
    return States.MAIN_MENU

async def start_level_test(update, context):
    # Импортируем и запускаем модуль тестирования уровня
    from modules.level_test import start_level_test as start_test
    return await start_test(update, context)

async def show_safety_rules(update, context):
    # Импортируем и запускаем модуль безопасности
    from modules.safety import show_safety_rules as show_safety
    return await show_safety(update, context)

async def handle_locations(update, context):
    user_id = update.effective_user.id
    user_lang = language_manager.get_user_language(user_id)
    
    locations_text = language_manager.get_text(user_id, 'locations.title')
    
    for loc_id, loc_data in LOCATIONS.items():
        location_name = loc_data['names'].get(user_lang, loc_data['names']['en'])
        description = loc_data['descriptions'].get(user_lang, loc_data['descriptions']['en'])
        locations_text += f"\n\n📍 *{location_name}*\n{description}"
    
    await update.message.reply_text(locations_text, parse_mode='Markdown', reply_markup=get_main_menu(user_id))
    return States.MAIN_MENU

async def handle_contacts(update, context):
    user_id = update.effective_user.id
    user_lang = language_manager.get_user_language(user_id)
    
    contacts_text = language_manager.get_text(user_id, 'contacts.info')
    
    if user_lang == 'ru':
        contacts_text += "\n\n📞 *Телефон:* +971 50 123 4567\n📧 *Email:* abdula@kiteschool.ae\n📍 *Адрес:* Дубай, Пляж Кайт Бич"
    elif user_lang == 'ar':
        contacts_text += "\n\n📞 *الهاتف:* 971 50 123 4567+\n📧 *البريد:* abdula@kiteschool.ae\n📍 *العنوان:* دبي، شاطئ كايت بيتش"
    else:
        contacts_text += "\n\n📞 *Phone:* +971 50 123 4567\n📧 *Email:* abdula@kiteschool.ae\n📍 *Address:* Dubai, Kite Beach"
    
    await update.message.reply_text(contacts_text, parse_mode='Markdown', reply_markup=get_main_menu(user_id))
    return States.MAIN_MENU

async def handle_language_selection(update, context):
    user_id = update.effective_user.id
    selected_language = update.message.text
    
    language_code = None
    for code, name in SUPPORTED_LANGUAGES.items():
        if name == selected_language:
            language_code = code
            break
    
    if language_code:
        await database_service.update_user_language(user_id, language_code)
        language_manager.set_user_language(user_id, language_code)
        
        success_text = language_manager.get_text(user_id, 'language.changed')
        await update.message.reply_text(success_text, reply_markup=get_main_menu(user_id))
        return States.MAIN_MENU
    else:
        await update.message.reply_text("❌ Неверный выбор языка", reply_markup=get_language_keyboard())
        return States.LANGUAGE_SELECTION

async def handle_unknown_message(update, context):
    user_id = update.effective_user.id
    await update.message.reply_text(
        "❌ Неизвестная команда",
        reply_markup=get_main_menu(user_id)
    )
    return States.MAIN_MENU

async def error_handler(update, context):
    logger.error(f"Ошибка: {context.error}", exc_info=context.error)
    
    if update and update.effective_user:
        user_id = update.effective_user.id
        error_text = language_manager.get_text(user_id, 'errors.general')
        await update.message.reply_text(error_text, reply_markup=get_main_menu(user_id))
    
    return States.MAIN_MENU

def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN не найден!")
        return
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Обработчик начала
    application.add_handler(CommandHandler("start", start))
    
    # Обработчик выбора языка
    application.add_handler(MessageHandler(
        filters.TEXT & filters.Regex('^(Русский|English|العربية)$'),
        handle_language_selection
    ))
    
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
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown_message)
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
            ]
        },
        fallbacks=[
            CommandHandler("start", start),
            MessageHandler(filters.TEXT & filters.Regex('^🏠'), start)
        ],
        allow_reentry=True
    )
    
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    
    logger.info("🤖 Бот запущен с реальным прогнозом ветра!")
    application.run_polling()

if __name__ == '__main__':
    main()