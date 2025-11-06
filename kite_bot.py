#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import time
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, ConversationHandler
from services.admin import AdminManager
from config import KITE_KEY, SERVER_TIMEOUT, SUPPORTED_LANGUAGES, TEXTS
from services.language_manager import LanguageManager
from services.calendar import Calendar
from utils.helpers import get_main_menu, format_bookings_table, get_location_keyboard, get_location_confirmation_keyboard, get_user_confirmation_keyboard, get_back_keyboard, parse_location_choice, should_skip_location
from database import Database

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния ConversationHandler
START, AWAITING_LANGUAGE, MAIN_MENU, LANGUAGE_SELECTION = range(4)
BOOKING_DATE, BOOKING_TIME, BOOKING_NAME, BOOKING_LOCATION_CHOICE, BOOKING_CONFIRM, BOOKING_CONFIRM_EXISTING = range(4, 10)
LEVEL_TEST_START, LEVEL_TEST_Q1, LEVEL_TEST_Q2, LEVEL_TEST_Q3, LEVEL_TEST_Q4, LEVEL_TEST_Q5 = range(10, 16)

language_manager = LanguageManager()
db = Database()
calendar = Calendar(db)
admin_manager = AdminManager(db)

# Тексты для различных функций
SPOTS_INFO = """
🏄‍♂️ **ЛУЧШИЕ СПОТЫ ДЛЯ КАЙТСЕРФИНГА В ОАЭ:**

1. **Kite Beach Dubai** 🌊
   - Уровень: Все уровни
   - Особенности: Мелкая вода, ровный ветер
   - Лучшее время: С 10:00 до 18:00

2. **Kite Beach Abu Dhabi** 🏖️  
   - Уровень: Начинающие +
   - Особенности: Широкая пляжная зона
   - Лучшее время: Утренние часы

3. **Jebel Ali Kite Beach** 💨
   - Уровень: Продвинутые
   - Особенности: Сильный ровный ветер
   - Лучшее время: После 14:00

4. **Al Hamra Kite Beach** 🏝️
   - Уровень: Все уровни
   - Особенности: Красивая природа
   - Лучшее время: Весь день

5. **Sunset Beach Umm Al Quwain** 🌅
   - Уровень: Профи
   - Особенности: Закатные сессии
   - Лучшее время: Вечер
"""

SAFETY_GUIDE = """
🛟 **ТЕХНИКА БЕЗОПАСНОСТИ КАЙТСЕРФИНГА:**

**ОСНОВНЫЕ ПРАВИЛА:**
1. ✅ Всегда проверяйте оборудование перед выходом на воду
2. ✅ Используйте шлем и спасательный жилет  
3. ✅ Соблюдайте дистанцию с другими райдерами
4. ✅ Изучите систему быстрого отстрела
5. ✅ Проверяйте прогноз ветра и погоду

**ЧТО ДЕЛАТЬ В ЭКСТРЕННЫХ СИТУАЦИЯХ:**
- При потере доски: не паникуйте, поднимите руку
- При сильном ветре: используйте систему отстрела
- При попадании в ливень: немедленно выходите из воды

**ВАЖНО:** Всегда катайтесь в зоне, соответствующей вашему уровню!
"""

CONTACTS_INFO = """
📞 **КОНТАКТЫ АБДУЛЫ:**

**Телефон:** +971 564327509
**Telegram:** @abdula_kite_pro  
**Instagram:** @abdula_kite_dubai

**📍 Где нас найти:**
Основной спот: Kite Beach Dubai
Резервный спот: Kite Beach Abu Dhabi

**🕒 Часы работы:**
Ежедневно с 7:00 до 18:00
"""

GALLERY_MESSAGE = """
📸 **ГАЛЕРЕЯ И ВИДЕО**

Посмотрите наши последние фото и видео с занятий:

**Instagram:** @abdula_kite_dubai
**YouTube:** Abdula Kite Pro Lessons

Здесь вы найдете:
- Фото с занятий 📷
- Видео прогресса студентов 🎥  
- Трюки и техники катания 🏄‍♂️
- Обзоры оборудования 🔧

Следите за нашими обновлениями! ✨
"""
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    logger.info(f"User {user.first_name} ({user.id}) started the bot")
    
    # Для новых пользователей показываем кнопку START
    existing_user = db.get_user(user.id)
    if not existing_user:
        start_text = language_manager.get_text(user.id, 'start_button')
        start_keyboard = ReplyKeyboardMarkup([[start_text]], resize_keyboard=True, one_time_keyboard=True)
        
        welcome_messages = {
            'en': "👋 Welcome to Kite Bot!\n\nPress START to begin:",
            'ru': "👋 Добро пожаловать в Kite Bot!\n\nНажмите START чтобы начать:",
            'ar': "👋 أهلاً بك في بوت الكايت!\n\nاضغط ابدأ للبدء:"
        }
        user_lang = language_manager.get_user_language(user.id)
        welcome_text = welcome_messages.get(user_lang, welcome_messages['en'])
        
        await update.message.reply_text(welcome_text, reply_markup=start_keyboard)
        return START
    
    # Существующий пользователь - обычный поток
    db.save_user(
        user_id=user.id,
        name=user.first_name,
        telegram_username=user.username
    )
    
    welcome_text = language_manager.get_personalized_welcome(user.id)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu(language_manager, user.id)
    )
    return MAIN_MENU

async def handle_start_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатия кнопки START"""
    user = update.message.from_user
    text = update.message.text
    
    start_text = language_manager.get_text(user.id, 'start_button')
    if text == start_text:
        db.save_user(
            user_id=user.id,
            name=user.first_name,
            telegram_username=user.username
        )
        
        welcome_text = language_manager.get_text(user.id, 'welcome_detect')
        await update.message.reply_text(welcome_text)
        
        context.user_data['language_start_time'] = time.time()
        context.user_data['user_id'] = user.id
        return AWAITING_LANGUAGE
    
    return START

async def handle_language_detection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text
    
    db.save_user(
        user_id=user.id,
        name=user.first_name, 
        telegram_username=user.username
    )
    
    start_time = context.user_data.get('language_start_time', 0)
    if time.time() - start_time > SERVER_TIMEOUT:
        language_manager.set_user_language(user.id, 'en')
        timeout_text = language_manager.get_text(user.id, 'timeout_english')
        manual_text = language_manager.get_text(user.id, 'manual_language')
        
        await update.message.reply_text(timeout_text)
        await update.message.reply_text(
            manual_text,
            reply_markup=language_manager.get_language_keyboard()
        )
        return LANGUAGE_SELECTION
    
    try:
        detected_lang = await language_manager.detect_language_from_text(user.id, text)
        welcome_text = language_manager.get_personalized_welcome(user.id)
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=get_main_menu(language_manager, user.id)
        )
        return MAIN_MENU
        
    except Exception as e:
        logger.error(f"Language detection failed: {e}")
        language_manager.set_user_language(user.id, 'en')
        busy_text = language_manager.get_text(user.id, 'ai_busy')
        
        await update.message.reply_text(busy_text)
        await update.message.reply_text(
            language_manager.get_personalized_welcome(user.id),
            reply_markup=get_main_menu(language_manager, user.id)
        )
        return MAIN_MENU

async def handle_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    language_code = query.data.replace('lang_', '')
    
    db.save_user(
        user_id=user.id,
        telegram_username=user.username
    )
    
    language_manager.set_user_language(user.id, language_code)
    
    changed_text = language_manager.get_text(user.id, 'language_changed')
    lang_name = SUPPORTED_LANGUAGES.get(language_code, 'English 🇺🇸')
    
    await query.edit_message_text(f"✅ {changed_text.format(lang_name)}")
    
    welcome_text = language_manager.get_personalized_welcome(user.id)
    
    await context.bot.send_message(
        chat_id=user.id,
        text=welcome_text,
        reply_markup=get_main_menu(language_manager, user.id)
    )
    return MAIN_MENU

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text
    
    menu_booking = language_manager.get_text(user.id, 'menu_booking')
    menu_level_test = language_manager.get_text(user.id, 'menu_level_test')
    menu_locations = language_manager.get_text(user.id, 'menu_locations')
    menu_safety = language_manager.get_text(user.id, 'menu_safety')
    menu_contacts = language_manager.get_text(user.id, 'menu_contacts')
    menu_gallery = language_manager.get_text(user.id, 'menu_gallery')
    menu_language = language_manager.get_text(user.id, 'menu_language')
    home_button = language_manager.get_text(user.id, 'home_button')
    
    # Проверяем кнопку Домой
    if text == home_button:
        welcome_text = language_manager.get_personalized_welcome(user.id)
        await update.message.reply_text(
            welcome_text,
            reply_markup=get_main_menu(language_manager, user.id)
        )
        return MAIN_MENU
    
    if text == menu_booking:
        return await start_booking(update, context)
        
    elif text == menu_level_test:
        return await start_level_test(update, context)
        
    elif text == menu_locations:
        await show_locations(update, context)
        return MAIN_MENU
        
    elif text == menu_safety:
        await show_safety(update, context)
        return MAIN_MENU
        
    elif text == menu_contacts:
        await show_contacts(update, context)
        return MAIN_MENU
        
    elif text == menu_gallery:
        await show_gallery(update, context)
        return MAIN_MENU
        
    elif text == menu_language:
        await update.message.reply_text(
            language_manager.get_text(user.id, 'manual_language'),
            reply_markup=language_manager.get_language_keyboard()
        )
        return LANGUAGE_SELECTION
        
    else:
        await update.message.reply_text(
            language_manager.get_text(user.id, 'use_menu_buttons'),
            reply_markup=get_main_menu(language_manager, user.id)
        )
    return MAIN_MENU
async def start_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    
    # Очистка предыдущих данных
    context.user_data.pop('selected_times', None)
    context.user_data.pop('selected_date', None)
    
    # Показ существующих бронирований
    bookings = db.get_user_bookings(user.id)
    bookings_table = format_bookings_table(bookings)
    await update.message.reply_text(bookings_table)
    
    # Показ календаря
    calendar_markup = calendar.generate_calendar()
    choose_date_text = language_manager.get_text(user.id, 'choose_date')
    await update.message.reply_text(
        choose_date_text,
        reply_markup=calendar_markup
    )
    return BOOKING_DATE

async def show_locations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    await update.message.reply_text(SPOTS_INFO)
    return MAIN_MENU

async def show_safety(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    await update.message.reply_text(SAFETY_GUIDE)
    return MAIN_MENU

async def show_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    await update.message.reply_text(CONTACTS_INFO)
    return MAIN_MENU

async def show_gallery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    await update.message.reply_text(GALLERY_MESSAGE)
    return MAIN_MENU

async def handle_booking_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "cal_cancel":
        await query.edit_message_text("❌ Запись отменена")
        return MAIN_MENU
    
    elif data.startswith("cal_prev_") or data.startswith("cal_next_"):
        parts = data.split("_")
        year = int(parts[2])
        month = int(parts[3])
        calendar_markup = calendar.generate_calendar(year, month)
        await query.edit_message_reply_markup(reply_markup=calendar_markup)
        return BOOKING_DATE
    
    elif data.startswith("cal_day_"):
        date_str = data.replace("cal_day_", "").replace("_", "-")
        context.user_data['selected_date'] = date_str
        context.user_data['selected_times'] = []
        
        time_markup = calendar.get_available_time_slots(date_str, [])
        time_message = calendar.get_time_selection_message(date_str, [])
        
        await query.edit_message_text(time_message, reply_markup=time_markup)
        return BOOKING_TIME
    return BOOKING_DATE

async def handle_booking_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    date = context.user_data.get('selected_date')
    
    if not date:
        await query.edit_message_text("❌ Ошибка: дата не выбрана")
        return MAIN_MENU
    
    if data == "cal_back":
        calendar_markup = calendar.generate_calendar()
        choose_date_text = language_manager.get_text(query.from_user.id, 'choose_date')
        await query.edit_message_text(choose_date_text, reply_markup=calendar_markup)
        return BOOKING_DATE
    
    elif data.startswith("time_") and data != "time_booked":
        parts = data.split("_")
        time_slot = parts[2]
        selected_times = context.user_data.get('selected_times', [])
        
        if time_slot in selected_times:
            selected_times.remove(time_slot)
        else:
            selected_times.append(time_slot)
        
        selected_times.sort()
        context.user_data['selected_times'] = selected_times
        
        time_markup = calendar.get_available_time_slots(date, selected_times)
        time_message = calendar.get_time_selection_message(date, selected_times)
        await query.edit_message_text(time_message, reply_markup=time_markup)
        return BOOKING_TIME
    
    elif data.startswith("confirm_booking_"):
        if not context.user_data.get('selected_times'):
            await query.answer("❌ Выберите хотя бы один временной слот", show_alert=True)
            return BOOKING_TIME
        
        selected_times = context.user_data['selected_times']
        user = query.from_user
        
        # Получаем данные пользователя из базы
        user_data = db.get_user(user.id)
        user_lang = language_manager.get_user_language(user.id)
        
        if user_data and user_data[1]:  # Если пользователь существует и есть имя
            user_name = user_data[1]
            context.user_data['user_name'] = user_name
            
            # Показываем форму с предзаполненными данными
            user_info_ar = f"""
📋 **بياناتك:**

👤 الاسم: {user_name}
📞 الهاتف: {user_data[3] or 'غير محدد'}
🏆 المستوى: {user_data[5] or 'غير محدد'}

📅 التاريخ: {date}
🕐 الوقت: {', '.join(selected_times)}

اختر الإجراء:
"""
            user_info_ru = f"""
📋 **ВАШИ ДАННЫЕ:**

👤 Имя: {user_name}
📞 Телефон: {user_data[3] or 'Не указан'}
🏆 Уровень: {user_data[5] or 'Не указан'}

📅 Дата: {date}
🕐 Время: {', '.join(selected_times)}

Выберите действие:
"""
            user_info_en = f"""
📋 **YOUR DATA:**

👤 Name: {user_name}
📞 Phone: {user_data[3] or 'Not specified'}
🏆 Level: {user_data[5] or 'Not specified'}

📅 Date: {date}
🕐 Time: {', '.join(selected_times)}

Choose action:
"""
            user_info = user_info_ar if user_lang == 'ar' else user_info_ru if user_lang == 'ru' else user_info_en
            
            await query.edit_message_text(user_info)
            confirmation_keyboard = get_user_confirmation_keyboard(language_manager, user.id)
            confirm_text = "Подтвердите данные или отредактируйте:" if user_lang == 'ru' else "Confirm data or edit:" if user_lang == 'en' else "قم بتأكيد البيانات أو تعديلها:"
            await context.bot.send_message(
                chat_id=user.id,
                text=confirm_text,
                reply_markup=confirmation_keyboard
            )
            return BOOKING_CONFIRM_EXISTING
        else:
            # Новый пользователь - стандартная форма
            name_prompt = language_manager.get_text(user.id, 'enter_name')
            await query.edit_message_text(
                f"📝 {name_prompt}\n\n📅 {date}\n🕐 {', '.join(selected_times)}"
            )
            return BOOKING_NAME
    
    return BOOKING_TIME

async def handle_booking_confirm_existing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка подтверждения данных существующим пользователем"""
    user = update.message.from_user
    choice = update.message.text
    user_lang = language_manager.get_user_language(user.id)
    
    confirm_texts = ["✅ подтвердить данные", "✅ confirm data", "✅ تأكيد البيانات"]
    edit_texts = ["✏️ редактировать данные", "✏️ edit data", "✏️ تعديل البيانات"]
    cancel_texts = ["❌ отменить запись", "❌ cancel booking", "❌ إلغاء الحجز"]
    
    if any(confirm_text in choice.lower() for confirm_text in confirm_texts):
        # Используем данные из базы
        user_data = db.get_user(user.id)
        context.user_data['user_name'] = user_data[1]
        
        # Переходим к выбору локации
        location_confirmation_keyboard = get_location_confirmation_keyboard(language_manager, user.id)
        location_prompt = "Хотите выбрать конкретную локацию для занятия?" if user_lang == 'ru' else "Do you want to choose a specific location for the lesson?" if user_lang == 'en' else "هل تريد اختيار موقع محدد للدرس؟"
        
        await update.message.reply_text(
            f"Отлично, {user_data[1]}! 🏄‍♂️\n\n{location_prompt}",
            reply_markup=location_confirmation_keyboard
        )
        return BOOKING_LOCATION_CHOICE
        
    elif any(edit_text in choice.lower() for edit_text in edit_texts):
        name_prompt = language_manager.get_text(user.id, 'enter_name')
        await update.message.reply_text(name_prompt)
        return BOOKING_NAME
        
    elif any(cancel_text in choice.lower() for cancel_text in cancel_texts):
        await update.message.reply_text(
            "❌ Запись отменена",
            reply_markup=get_main_menu(language_manager, user.id)
        )
        return MAIN_MENU
    
    return BOOKING_CONFIRM_EXISTING


async def handle_booking_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_name = update.message.text
    
    if await is_menu_command(user_name, user.id):
        return await handle_main_menu(update, context)
    
    db.save_user(user_id=user.id, name=user_name, telegram_username=user.username)
    context.user_data['user_name'] = user_name
    
    location_confirmation_keyboard = get_location_confirmation_keyboard(language_manager, user.id)
    user_lang = language_manager.get_user_language(user.id)
    location_prompt = "Хотите выбрать конкретную локацию для занятия?" if user_lang == 'ru' else "Do you want to choose a specific location for the lesson?" if user_lang == 'en' else "هل تريد اختيار موقع محدد للدرس؟"
    
    await update.message.reply_text(
        f"Отлично, {user_name}! 🏄‍♂️\n\n{location_prompt}",
        reply_markup=location_confirmation_keyboard
    )
    return BOOKING_LOCATION_CHOICE

async def handle_booking_location_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    choice = update.message.text
    user_lang = language_manager.get_user_language(user.id)
    
    if await is_menu_command(choice, user.id):
        return await handle_main_menu(update, context)
    
    yes_keywords = ["да", "выбрать", "✅", "نعم", "اختر", "yes", "choose"]
    if any(keyword in choice.lower() for keyword in yes_keywords):
        location_keyboard = get_location_keyboard(language_manager, user.id)
        
        if user_lang == 'ar':
            location_text = "🌊 اختر الموقع (بالرقم 1-5):\n1. كايت بيتش دبي (جميع المستويات)\n2. كايت بيتش أبوظبي (مبتدئ+)\n3. جبل علي كايت بيتش (متقدم)\n4. الحمرا كايت بيتش (جميع المستويات)\n5. سانسيت بيتش أم القيوين (محترف)\n\nأدخل الرقم أو الاسم:"
        elif user_lang == 'en':
            location_text = "🌊 Choose location (number 1-5):\n1. Kite Beach Dubai (all levels)\n2. Kite Beach Abu Dhabi (beginner+)\n3. Jebel Ali Kite Beach (advanced)\n4. Al Hamra Kite Beach (all levels)\n5. Sunset Beach Umm Al Quwain (pro)\n\nEnter number or name:"
        else:
            location_text = "🌊 Выберите локацию (цифрой 1-5):\n1. Kite Beach Dubai (все уровни)\n2. Kite Beach Abu Dhabi (начинающие+)\n3. Jebel Ali Kite Beach (продвинутые)\n4. Al Hamra Kite Beach (все уровни)\n5. Sunset Beach Umm Al Quwain (профи)\n\nВведите цифру или название:"
        
        await update.message.reply_text(location_text, reply_markup=location_keyboard)
        return BOOKING_CONFIRM
    else:
        context.user_data['location'] = "Не указана" if user_lang == 'ru' else "Not specified" if user_lang == 'en' else "غير محدد"
        return await finalize_booking(update, context)

async def handle_booking_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    location_choice = update.message.text
    
    if await is_menu_command(location_choice, user.id):
        return await handle_main_menu(update, context)
    
    location = parse_location_choice(location_choice)
    if should_skip_location(location_choice) or not location or location == location_choice:
        user_lang = language_manager.get_user_language(user.id)
        context.user_data['location'] = "Не указана" if user_lang == 'ru' else "Not specified" if user_lang == 'en' else "غير محدد"
    else:
        context.user_data['location'] = location
    
    return await finalize_booking(update, context)

async def finalize_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    date = context.user_data.get('selected_date')
    selected_times = context.user_data.get('selected_times', [])
    user_name = context.user_data.get('user_name')
    location = context.user_data.get('location', 'Не указана')
    user_lang = language_manager.get_user_language(user.id)
    
    logger.info(f"🔧 Finalize booking: {user_name} on {date} at {selected_times}")
    
    if not date or not selected_times or not user_name:
        error_text = language_manager.get_text(user.id, 'error_insufficient_data')
        logger.error(f"{error_text} - date: {date}, times: {selected_times}, name: {user_name}")
        await update.message.reply_text(error_text)
        return MAIN_MENU
    
    success_count = 0
    try:
        # Сохраняем каждое бронирование отдельно
        for time_slot in selected_times:
            success = db.save_booking(
                date=date,
                time=time_slot,
                user_id=user.id,
                student_name=user_name,
                location=location
            )
            if success:
                success_count += 1
                logger.info(f"✅ Slot saved: {date} {time_slot}")
            else:
                logger.error(f"❌ Failed to save slot: {date} {time_slot}")
        
        if success_count == len(selected_times):
            logger.info(f"🎉 ALL bookings saved: {user_name} on {date} at {selected_times}")
        else:
            logger.warning(f"⚠️ Partial success: {success_count}/{len(selected_times)} slots saved")
            
    except Exception as e:
        logger.error(f"❌ Critical error in finalize_booking: {e}")
        error_text = language_manager.get_text(user.id, 'error_saving')
        await update.message.reply_text(error_text)
        return MAIN_MENU
    
    # Показываем подтверждение
    user_name_display = language_manager.get_user_name(user.id) or user_name
    
    if user_lang == 'ar':
        success_text = f"""
✅ تم تأكيد الحجز، {user_name_display}!

📅 التاريخ: {date}
🕐 الوقت: {', '.join(selected_times)}
👤 الاسم: {user_name}
🌊 الموقع: {location}

سيتصل بك عبدلة للتأكيد 📱
الهاتف: +971 564327509
Telegram: @abdula_kite_pro
"""
    elif user_lang == 'en':
        success_text = f"""
✅ Booking confirmed, {user_name_display}!

📅 Date: {date}
🕐 Time: {', '.join(selected_times)}
👤 Name: {user_name}
🌊 Location: {location}

Abdula will contact you for confirmation 📱
Phone: +971 564327509
Telegram: @abdula_kite_pro
"""
    else:
        success_text = f"""
✅ Запись подтверждена, {user_name_display}!

📅 Дата: {date}
🕐 Время: {', '.join(selected_times)}
👤 Имя: {user_name}
🌊 Локация: {location}

Абдула свяжется с вами для подтверждения 📱
Телефон: +971 564327509
Telegram: @abdula_kite_pro
"""
    
    await update.message.reply_text(
        success_text,
        reply_markup=get_main_menu(language_manager, user.id)
    )
    
    logger.info(f"📅 НОВАЯ ЗАПИСЬ: {user_name} на {date} в {', '.join(selected_times)} в {location}")
    
    # Очистка данных и возврат в главное меню
    context.user_data.clear()
    return MAIN_MENU

async def start_level_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    test_text = language_manager.get_text(user.id, 'level_test')
    await update.message.reply_text(test_text)
    
    # Первый вопрос теста
    q1_text = "1. **Опыт катания:**\n- Никогда не катался(ась) (3)\n- Был(а) несколько раз (2)\n- Катаюсь регулярно (1)\n\nОтветьте цифрой:"
    await update.message.reply_text(q1_text)
    
    context.user_data['level_test_answers'] = []
    return LEVEL_TEST_Q1

async def handle_level_test_q1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text
    
    if await is_menu_command(text, user.id):
        return await handle_main_menu(update, context)
    
    if 'level_test_answers' not in context.user_data:
        context.user_data['level_test_answers'] = []
    context.user_data['level_test_answers'].append(text)
    
    q2_text = "2. **Управление:**\n- Могу управлять одной рукой (1)\n- Нужно две руки для контроля (2)\n- Теряю контроль при управлении (3)\n\nОтветьте цифрой:"
    await update.message.reply_text(q2_text)
    return LEVEL_TEST_Q2

async def handle_level_test_q2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text
    
    if await is_menu_command(text, user.id):
        return await handle_main_menu(update, context)
    
    if 'level_test_answers' not in context.user_data:
        context.user_data['level_test_answers'] = []
    context.user_data['level_test_answers'].append(text)
    
    q3_text = "3. **Body dragging:**\n- Могу body drag против ветра (1)\n- Могу body drag по ветру (2)\n- Не умею body drag (3)\n\nОтветьте цифрой:"
    await update.message.reply_text(q3_text)
    return LEVEL_TEST_Q3

async def handle_level_test_q3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text
    
    if await is_menu_command(text, user.id):
        return await handle_main_menu(update, context)
    
    if 'level_test_answers' not in context.user_data:
        context.user_data['level_test_answers'] = []
    context.user_data['level_test_answers'].append(text)
    
    q4_text = "4. **Водный старт:**\n- Стартую с 1-2 попыток (1)\n- Стартую с 3-5 попыток (2)\n- Не умею вставать на доску (3)\n\nОтветьте цифрой:"
    await update.message.reply_text(q4_text)
    return LEVEL_TEST_Q4

async def handle_level_test_q4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text
    
    if await is_menu_command(text, user.id):
        return await handle_main_menu(update, context)
    
    if 'level_test_answers' not in context.user_data:
        context.user_data['level_test_answers'] = []
    context.user_data['level_test_answers'].append(text)
    
    q5_text = "5. **Навыки катания:**\n- Могу глиссировать уверенно (1)\n- Могу делать повороты (2)\n- Могу прыгать и делать трюки (3)\n\nОтветьте цифрой:"
    await update.message.reply_text(q5_text)
    return LEVEL_TEST_Q5

async def handle_level_test_q5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text
    
    if await is_menu_command(text, user.id):
        return await handle_main_menu(update, context)
    
    if 'level_test_answers' not in context.user_data:
        context.user_data['level_test_answers'] = []
    context.user_data['level_test_answers'].append(text)
    
    # Расчет результатов
    answers = context.user_data['level_test_answers']
    total_score = sum(int(ans) for ans in answers if ans.isdigit())
    
    if total_score <= 8:
        level = "ПРОДВИНУТЫЙ 🏄‍♂️"
        recommendation = "Рекомендуем споты: Jebel Ali, Sunset Beach"
    elif total_score <= 12:
        level = "СРЕДНИЙ ⭐"
        recommendation = "Рекомендуем споты: Kite Beach Dubai, Al Hamra"
    else:
        level = "НОВИЧОК 🌱"
        recommendation = "Рекомендуем споты: Kite Beach Abu Dhabi для начинающих"
    
    user_name = language_manager.get_user_name(user.id) or "друг"
    
    result_text = f"""
🎯 **РЕЗУЛЬТАТ ТЕСТА УРОВНЯ {user_name.upper()}:**

🏆 Ваш уровень: {level}

📊 Баллы: {total_score}/15

💡 {recommendation}

📅 Запишитесь на урок с Абдулой для улучшения навыков!
"""
    
    await update.message.reply_text(
        result_text,
        reply_markup=get_main_menu(language_manager, user.id)
    )
    
    db.save_user(user.id, level=level)
    return MAIN_MENU

async def is_menu_command(text: str, user_id: int) -> bool:
    menu_items = [
        language_manager.get_text(user_id, 'menu_booking'),
        language_manager.get_text(user_id, 'menu_level_test'),
        language_manager.get_text(user_id, 'menu_locations'),
        language_manager.get_text(user_id, 'menu_safety'),
        language_manager.get_text(user_id, 'menu_contacts'),
        language_manager.get_text(user_id, 'menu_gallery'),
        language_manager.get_text(user_id, 'menu_language'),
        language_manager.get_text(user_id, 'home_button')
    ]
    return text in menu_items

async def change_language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    await update.message.reply_text(
        language_manager.get_text(user.id, 'manual_language'),
        reply_markup=language_manager.get_language_keyboard()
    )
    return LANGUAGE_SELECTION

async def home_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /home"""
    user = update.message.from_user
    welcome_text = language_manager.get_personalized_welcome(user.id)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu(language_manager, user.id)
    )
    return MAIN_MENU

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if not admin_manager.is_admin(user.id):
        await update.message.reply_text("❌ Доступ запрещен")
        return MAIN_MENU
    
    stats = admin_manager.get_today_stats()
    recent_bookings = admin_manager.get_recent_bookings(5)
    user_stats = admin_manager.get_user_stats()
    all_users = db.get_all_users()
    
    # Форматируем бронирования
    bookings_text = ""
    for booking in recent_bookings:
        booking_id, date, time, name, status, username = booking
        status_emoji = "✅" if status == "confirmed" else "⏳" if status == "booked" else "❌"
        username_display = f"(@{username})" if username else ""
        bookings_text += f"• {status_emoji} {date} {time} - {name} {username_display}\n"
    
    # Форматируем статистику по языкам
    user_stats_text = "\n".join([f"• {lang}: {count}" for lang, count in user_stats])
    
    # Форматируем пользователей
    users_details = []
    for user_data in all_users[:10]:
        user_id, name, telegram_username, phone, language, level, created_at = user_data
        user_info = f"👤 {name or 'No name'}"
        if telegram_username:
            user_info += f" (@{telegram_username})"
        user_info += f" | {language} | {level or 'No level'}"
        users_details.append(user_info)
    
    users_text = "\n".join(users_details) if users_details else "Нет пользователей"
    
    # Статистика по статусам
    status_stats_text = ""
    for status, count in stats['status_stats'].items():
        status_emoji = "✅" if status == "confirmed" else "⏳" if status == "booked" else "❌"
        status_stats_text += f"• {status_emoji} {status}: {count}\n"
    
    admin_text = f"""
👑 **ABDULLAH ADMIN PANEL**

📊 **TODAY:**
• Bookings: {stats['today_bookings']}
• Total users: {stats['total_users']} 
• Total bookings: {stats['total_bookings']}

📈 **STATUS STATS:**
{status_stats_text}

🌐 **LANGUAGES:**
{user_stats_text}

📋 **RECENT BOOKINGS:**
{bookings_text}

👥 **LAST USERS:**
{users_text}

⚡ **QUICK ACTIONS:**
/admin_stats - Full statistics
/bookings_today - Today's bookings
"""
    await update.message.reply_text(admin_text)
    return MAIN_MENU

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if not admin_manager.is_admin(user.id):
        await update.message.reply_text("❌ Доступ запрещен")
        return MAIN_MENU
    
    stats = admin_manager.get_today_stats()
    recent_bookings = admin_manager.get_recent_bookings(10)
    user_stats = admin_manager.get_user_stats()
    all_users = db.get_all_users()
    booking_stats = admin_manager.get_booking_stats_by_date(7)
    
    # Форматируем статистику по дням
    stats_by_date = ""
    for date, count in booking_stats:
        stats_by_date += f"• {date}: {count} bookings\n"
    
    users_details = []
    for user_data in all_users[:15]:
        user_id, name, telegram_username, phone, language, level, created_at = user_data
        user_info = f"• {name or 'No name'}"
        if telegram_username:
            user_info += f" (@{telegram_username})"
        user_info += f" | {language} | {level or 'No level'} | {created_at.split()[0]}"
        users_details.append(user_info)
    
    users_text = "\n".join(users_details)
    
    admin_stats_text = f"""
📈 **ПОЛНАЯ СТАТИСТИКА:**

👥 **ПОЛЬЗОВАТЕЛИ:** {stats['total_users']}
📅 **ЗАПИСИ:** {stats['total_bookings']} (сегодня: {stats['today_bookings']})

📊 **СТАТИСТИКА ЗА 7 ДНЕЙ:**
{stats_by_date}

🌐 **РАСПРЕДЕЛЕНИЕ ПО ЯЗЫКАМ:**
{user_stats_text}

👥 **ПОСЛЕДНИЕ ПОЛЬЗОВАТЕЛИ:**
{users_text}
"""
    await update.message.reply_text(admin_stats_text)
    return MAIN_MENU

async def bookings_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if not admin_manager.is_admin(user.id):
        await update.message.reply_text("❌ Доступ запрещен")
        return MAIN_MENU
    
    today = datetime.now().strftime('%Y-%m-%d')
    today_bookings = admin_manager.get_all_bookings(today)
    
    if not today_bookings:
        await update.message.reply_text(f"📅 На сегодня ({today}) нет бронирований")
        return MAIN_MENU
    
    bookings_text = f"📅 **БРОНИРОВАНИЯ НА СЕГОДНЯ ({today}):**\n\n"
    
    for booking in today_bookings:
        booking_id, date, time, name, status, username, phone = booking
        status_emoji = "✅" if status == "confirmed" else "⏳" if status == "booked" else "❌"
        username_display = f"(@{username})" if username else ""
        phone_display = f"📞 {phone}" if phone else ""
        bookings_text += f"{status_emoji} **{time}** - {name} {username_display} {phone_display}\n"
    
    await update.message.reply_text(bookings_text)
    return MAIN_MENU

def main():
    if not KITE_KEY:
        logger.error("❌ KITE_KEY not found in .env")
        return
    
    application = Application.builder().token(KITE_KEY).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            START: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_start_button)],
            AWAITING_LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_language_detection)],
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)],
            LANGUAGE_SELECTION: [CallbackQueryHandler(handle_language_selection, pattern='^lang_')],
            BOOKING_DATE: [CallbackQueryHandler(handle_booking_date, pattern='^cal_')],
            BOOKING_TIME: [CallbackQueryHandler(handle_booking_time, pattern='^time_|^cal_back|^confirm_booking_|^time_booked')],
            BOOKING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_booking_name)],
            BOOKING_LOCATION_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_booking_location_choice)],
            BOOKING_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_booking_confirm)],
            BOOKING_CONFIRM_EXISTING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_booking_confirm_existing)],
            LEVEL_TEST_Q1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_level_test_q1)],
            LEVEL_TEST_Q2: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_level_test_q2)],
            LEVEL_TEST_Q3: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_level_test_q3)],
            LEVEL_TEST_Q4: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_level_test_q4)],
            LEVEL_TEST_Q5: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_level_test_q5)]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('language', change_language_command))
    application.add_handler(CommandHandler('home', home_command))
    application.add_handler(CommandHandler('menu', home_command))
    application.add_handler(CommandHandler('admin', admin_panel))
    application.add_handler(CommandHandler('admin_stats', admin_stats))
    application.add_handler(CommandHandler('bookings_today', bookings_today))
    
    print("🚀 Kite Bot UPDATED launched!")
    application.run_polling()

if __name__ == '__main__':
    main()
