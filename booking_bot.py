#!/usr/bin/env python3
# booking_bot.py - бот с полной системой бронирования
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import random

from config.settings import TELEGRAM_BOT_TOKEN, LOCATIONS, SCHEDULE, CONTACTS
from config.constants import States
from services import language_manager, database_service

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Класс для управления календарем
class BookingCalendar:
    def __init__(self):
        self.time_slots = SCHEDULE['time_slots']
    
    def generate_calendar(self, year=None, month=None):
        """Генерация календаря на месяц"""
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
    
    def get_calendar_keyboard(self, year=None, month=None):
        """Создание клавиатуры календаря"""
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
                    # Демо: случайный прогноз ветра
                    wind_speed = random.uniform(5, 25)
                    if 12 <= wind_speed <= 20:
                        label = f"🟢{date_label}🌪"
                    elif wind_speed < 8:
                        label = f"🔴{date_label}"
                    elif wind_speed > 25:
                        label = f"🔴{date_label}💨"
                    else:
                        label = f"🟡{date_label}"
                    
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
    
    def get_time_keyboard(self, date):
        """Клавиатура выбора времени"""
        keyboard = []
        
        # Группируем время по периодам
        morning_slots = [t for t in self.time_slots if int(t.split(':')[0]) < 12]
        afternoon_slots = [t for t in self.time_slots if 12 <= int(t.split(':')[0]) < 17]
        evening_slots = [t for t in self.time_slots if int(t.split(':')[0]) >= 17]
        
        # Утренние слоты
        morning_row = []
        for time in morning_slots:
            # Демо: 80% слотов свободны
            if random.random() < 0.8:
                label = f"🟢{time}"
            else:
                label = f"🟡{time}"
            morning_row.append(InlineKeyboardButton(label, callback_data=f"time_{time}"))
            if len(morning_row) == 3:
                keyboard.append(morning_row)
                morning_row = []
        if morning_row:
            keyboard.append(morning_row)
        
        # Дневные слоты
        afternoon_row = []
        for time in afternoon_slots:
            if random.random() < 0.8:
                label = f"🟢{time}"
            else:
                label = f"🟡{time}"
            afternoon_row.append(InlineKeyboardButton(label, callback_data=f"time_{time}"))
            if len(afternoon_row) == 3:
                keyboard.append(afternoon_row)
                afternoon_row = []
        if afternoon_row:
            keyboard.append(afternoon_row)
        
        # Вечерние слоты
        evening_row = []
        for time in evening_slots:
            if random.random() < 0.8:
                label = f"🟢{time}"
            else:
                label = f"🟡{time}"
            evening_row.append(InlineKeyboardButton(label, callback_data=f"time_{time}"))
        if evening_row:
            keyboard.append(evening_row)
        
        # Легенда
        legend = [
            InlineKeyboardButton("🟢 Свободно", callback_data="ignore"),
            InlineKeyboardButton("🟡 Занято", callback_data="ignore")
        ]
        keyboard.append(legend)
        
        # Навигация
        nav_buttons = [
            InlineKeyboardButton("◀️ Назад к датам", callback_data="back_to_dates"),
            InlineKeyboardButton("❌ Отмена", callback_data="cancel_booking")
        ]
        keyboard.append(nav_buttons)
        
        return InlineKeyboardMarkup(keyboard)

# Инициализация календаря
calendar_service = BookingCalendar()

# Функции клавиатур
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
    languages = language_manager.get_supported_languages_dict()
    language_list = list(languages.values())
    
    keyboard = [
        [language_list[0], language_list[1]],
        [language_list[2]]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_back_keyboard(user_id: int):
    """Клавиатура с кнопкой Назад"""
    back_text = language_manager.get_text(user_id, 'menu.back')
    return ReplyKeyboardMarkup([[back_text]], resize_keyboard=True)

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
        confirm_text, cancel_text = "✅ Подтвердить", "❌ Отменить"
    elif user_lang == 'ar':
        confirm_text, cancel_text = "✅ تأكيد", "❌ إلغاء"
    else:
        confirm_text, cancel_text = "✅ Confirm", "❌ Cancel"
    return ReplyKeyboardMarkup([[confirm_text, cancel_text]], resize_keyboard=True)

# Основные обработчики
async def start(update, context):
    """Обработчик команды /start"""
    user = update.effective_user
    user_id = user.id
    
    logger.info(f"👋 User: {user_id} - {user.first_name}")

    # Используем новый get_or_create_user метод
    user_obj = await database_service.get_or_create_user(user)
    
    welcome_text = language_manager.get_text(user_id, 'welcome.personalized', name=user.first_name)
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
        choose_text = language_manager.get_text(user_id, 'language.choose')
        await update.message.reply_text(choose_text, reply_markup=reply_markup)
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
    
    choose_date_text = language_manager.get_text(user_id, 'booking.choose_date_calendar')
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
                await query.edit_message_text(
                    query.message.text,
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Calendar error: {e}")
                await query.answer("❌ Ошибка календаря", show_alert=True)
    
    elif data.startswith('book_date_'):
        # Выбор даты
        date = data.replace('book_date_', '')
        context.user_data['booking_date'] = date
        
        # Получаем клавиатуру времени
        time_keyboard = calendar_service.get_time_keyboard(date)
        
        # Форматируем дату для сообщения
        selected_date = datetime.strptime(date, "%Y-%m-%d")
        formatted_date = selected_date.strftime("%d.%m.%Y")
        
        time_message = f"📅 **Выбрана дата: {formatted_date}**\n\n🕐 Выберите время для занятия:"
        
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
    
    # Проверяем, что время свободно (демо-логика)
    if "🟡" in query.message.text:  # Если слот занят
        await query.answer("❌ Это время уже занято", show_alert=True)
        return
    
    date = context.user_data.get('booking_date')
    if not date:
        await query.answer("❌ Ошибка: дата не выбрана", show_alert=True)
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

async def handle_location_selection(update, context):
    """Обработчик выбора локации"""
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
    """Обработчик ввода имени"""
    user_id = update.effective_user.id
    user_name = update.message.text.strip()
    
    if len(user_name) < 2:
        await update.message.reply_text("❌ Имя слишком короткое", reply_markup=get_back_keyboard(user_id))
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
    """Обработчик подтверждения бронирования"""
    user_id = update.effective_user.id
    user_response = update.message.text
    user_lang = language_manager.get_user_language(user_id)
    
    confirm_keywords = ['confirm', 'подтвердить', 'تأكيد']
    cancel_keywords = ['cancel', 'отменить', 'إلغاء']
    
    if any(keyword in user_response.lower() for keyword in confirm_keywords):
        booking_data = context.user_data
        
        # Создаем бронирование в базе данных
        booking = await database_service.create_booking(
            telegram_id=user_id,
            user_name=booking_data['booking_name'],
            booking_date=booking_data['booking_date'],
            booking_time=booking_data['booking_time'],
            location=booking_data['booking_location'],
            wind_forecast=f"{random.uniform(5, 25):.1f} knots",  # Демо-прогноз
            price=75.00,  # Демо-цена
            duration=60
        )
        
        if booking:
            booking_details = format_booking_details(booking, user_lang)
            confirm_text = language_manager.get_text(user_id, 'booking.confirm_booking')
            await update.message.reply_text(
                f"🎉 {confirm_text}\n{booking_details}", 
                parse_mode='Markdown', 
                reply_markup=get_main_menu(user_id)
            )
            context.user_data.clear()
            return States.MAIN_MENU
        else:
            error_text = language_manager.get_text(user_id, 'errors.saving_error')
            await update.message.reply_text(error_text, reply_markup=get_main_menu(user_id))
            return States.MAIN_MENU
            
    elif any(keyword in user_response.lower() for keyword in cancel_keywords):
        cancel_text = "❌ Бронирование отменено"
        await update.message.reply_text(cancel_text, reply_markup=get_main_menu(user_id))
        return States.MAIN_MENU
    else:
        await update.message.reply_text("❌ Подтвердите или отмените", reply_markup=get_confirmation_keyboard(user_id))
        return States.BOOKING_CONFIRM

def format_booking_details(booking: dict, language: str) -> str:
    """Форматировать детали бронирования"""
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

💨 Прогноз ветра: {booking.get('wind_forecast', 'Н/Д')}
💵 Стоимость: ${booking.get('price', 0)}
⏱ Длительность: {booking.get('duration', 60)} мин

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

💨 Wind forecast: {booking.get('wind_forecast', 'N/A')}
💵 Price: ${booking.get('price', 0)}
⏱ Duration: {booking.get('duration', 60)} min

📞 **Abdula will contact you to confirm**
⏰ Contact hours: 7:00 AM to 6:00 PM

Save this information! ✨"""

async def show_main_menu(update, context):
    """Показать главное меню"""
    user_id = update.effective_user.id if hasattr(update, 'effective_user') else update.callback_query.from_user.id
    
    if hasattr(update, 'callback_query'):
        await update.callback_query.message.reply_text("Возврат в главное меню", reply_markup=get_main_menu(user_id))
    else:
        await update.message.reply_text("Возврат в главное меню", reply_markup=get_main_menu(user_id))
    return States.MAIN_MENU

async def handle_language_selection(update, context):
    """Обработка выбора языка"""
    user_id = update.effective_user.id
    text = update.message.text
    
    language_map = language_manager.get_supported_languages_dict()
    language_code = None
    
    for code, name in language_map.items():
        if name == text:
            language_code = code
            break
    
    if language_code:
        language_manager.set_user_language(user_id, language_code)
        await database_service.update_user(user_id, language=language_code, language_selected=True)
        
        confirmation = language_manager.get_text(user_id, 'language.changed')
        await update.message.reply_text(confirmation, reply_markup=get_main_menu(user_id))
        return States.MAIN_MENU
    else:
        await update.message.reply_text("❌ Неизвестный язык")
        return States.LANGUAGE_SELECTION

async def handle_contacts(update, context):
    """Обработчик контактов"""
    user_id = update.effective_user.id
    user_lang = language_manager.get_user_language(user_id)
    
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
    
    await update.message.reply_text(contacts_text, parse_mode='Markdown', reply_markup=get_main_menu(user_id))

async def handle_locations(update, context):
    """Обработчик локаций"""
    user_id = update.effective_user.id
    user_lang = language_manager.get_user_language(user_id)
    
    locations_text = ""
    for loc_id, loc_data in LOCATIONS.items():
        name = loc_data['names'].get(user_lang, loc_data['names']['en'])
        description = loc_data['description'].get(user_lang, loc_data['description']['en'])
        locations_text += f"📍 **{name}**\\n   - {description}\\n   - 🕒 {loc_data['best_time']}\\n\\n"
    
    await update.message.reply_text(locations_text, parse_mode='Markdown', reply_markup=get_main_menu(user_id))

async def cancel(update, context):
    """Отмена операции"""
    user_id = update.effective_user.id
    user_lang = language_manager.get_user_language(user_id)
    cancel_text = "Операция отменена"
    await update.message.reply_text(cancel_text, reply_markup=get_main_menu(user_id))
    return ConversationHandler.END

async def error_handler(update, context):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")

def main():
    """Основная функция запуска"""
    logger.info("🚀 Kite Bot с системой бронирования запускается...")
    
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(database_service.init_db())
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Conversation Handler с полной системой бронирования
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
                CallbackQueryHandler(handle_calendar_callback, pattern="^(calendar_|book_date_|cancel_booking|back_to_dates)")
            ],
            States.BOOKING_TIME: [
                CallbackQueryHandler(handle_calendar_callback, pattern="^(time_.*)")
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
    
    logger.info("✅ Бот с системой бронирования запущен!")
    application.run_polling()

if __name__ == '__main__':
    main()
