# utils/helpers.py
from datetime import datetime
from telegram import ReplyKeyboardMarkup

def get_main_menu(language_manager, user_id):
    menu_booking = language_manager.get_text(user_id, 'menu_booking')
    menu_level_test = language_manager.get_text(user_id, 'menu_level_test')
    menu_locations = language_manager.get_text(user_id, 'menu_locations')
    menu_safety = language_manager.get_text(user_id, 'menu_safety')
    menu_contacts = language_manager.get_text(user_id, 'menu_contacts')
    menu_gallery = language_manager.get_text(user_id, 'menu_gallery')
    menu_language = language_manager.get_text(user_id, 'menu_language')
    home_button = language_manager.get_text(user_id, 'home_button')
    
    keyboard = [
        [menu_booking, menu_level_test],
        [menu_locations, menu_safety],
        [menu_contacts, menu_gallery],
        [menu_language],
        [home_button]
    ]
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def format_bookings_table(bookings):
    if not bookings:
        return "📋 У вас пока нет записей на уроки"
    
    today = datetime.now().date()
    future_bookings = []
    past_bookings = []
    
    for booking in bookings:
        date_str, time_str, name, lesson_type, status = booking
        try:
            booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            continue
        
        if booking_date >= today:
            future_bookings.append(booking)
        else:
            past_bookings.append(booking)
    
    result = "📅 **ВАШИ БРОНИРОВАНИЯ**\n\n"
    
    if future_bookings:
        result += "🟢 **ПРЕДСТОЯЩИЕ:**\n"
        for booking in future_bookings[:5]:
            date_str, time_str, name, lesson_type, status = booking
            status_emoji = "✅" if status == "confirmed" else "⏳" if status == "booked" else "❌"
            result += f"{status_emoji} {date_str} 🕐 {time_str} - {name}\n"
        result += "\n"
    
    if past_bookings:
        result += "🔵 **ЗАВЕРШЕННЫЕ:**\n"
        for booking in past_bookings[:3]:
            date_str, time_str, name, lesson_type, status = booking
            result += f"✅ {date_str} 🕐 {time_str} - {name}\n"
    
    return result

def get_location_keyboard(language_manager, user_id):
    from telegram import ReplyKeyboardMarkup
    
    user_lang = language_manager.get_user_language(user_id)
    
    if user_lang == 'ar':
        keyboard = [
            ["1. كايت بيتش دبي"],
            ["2. كايت بيتش أبوظبي"], 
            ["3. جبل علي كايت بيتش"],
            ["4. الحمرا كايت بيتش"],
            ["5. سانسيت بيتش أم القيوين"],
            ["❌ لا، تخطى اختيار الموقع"]
        ]
    elif user_lang == 'en':
        keyboard = [
            ["1. Kite Beach Dubai"],
            ["2. Kite Beach Abu Dhabi"], 
            ["3. Jebel Ali Kite Beach"],
            ["4. Al Hamra Kite Beach"],
            ["5. Sunset Beach Umm Al Quwain"],
            ["❌ No, skip location selection"]
        ]
    else:
        keyboard = [
            ["1. Kite Beach Dubai"],
            ["2. Kite Beach Abu Dhabi"], 
            ["3. Jebel Ali Kite Beach"],
            ["4. Al Hamra Kite Beach"],
            ["5. Sunset Beach Umm Al Quwain"],
            ["❌ Нет, пропустить выбор локации"]
        ]
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_location_confirmation_keyboard(language_manager, user_id):
    from telegram import ReplyKeyboardMarkup
    
    user_lang = language_manager.get_user_language(user_id)
    
    if user_lang == 'ar':
        keyboard = [
            ["✅ نعم، اختر موقع"],
            ["❌ لا، تابع بدون موقع"]
        ]
    elif user_lang == 'en':
        keyboard = [
            ["✅ Yes, choose location"],
            ["❌ No, continue without location"]
        ]
    else:
        keyboard = [
            ["✅ Да, выбрать локацию"],
            ["❌ Нет, продолжить без локации"]
        ]
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_user_confirmation_keyboard(language_manager, user_id):
    from telegram import ReplyKeyboardMarkup
    
    user_lang = language_manager.get_user_language(user_id)
    
    if user_lang == 'ar':
        keyboard = [
            ["✅ تأكيد البيانات", "✏️ تعديل البيانات"],
            ["❌ إلغاء الحجز"]
        ]
    elif user_lang == 'en':
        keyboard = [
            ["✅ Confirm data", "✏️ Edit data"],
            ["❌ Cancel booking"]
        ]
    else:
        keyboard = [
            ["✅ Подтвердить данные", "✏️ Редактировать данные"],
            ["❌ Отменить запись"]
        ]
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_back_keyboard(language_manager, user_id):
    from telegram import ReplyKeyboardMarkup
    
    back_text = language_manager.get_text(user_id, 'back_button')
    home_text = language_manager.get_text(user_id, 'home_button')
    
    keyboard = [
        [back_text, home_text]
    ]
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def parse_location_choice(choice):
    location_map = {
        # English
        "1": "Kite Beach Dubai",
        "1.": "Kite Beach Dubai",
        "1. kite beach dubai": "Kite Beach Dubai",
        "1.kite beach dubai": "Kite Beach Dubai",
        "kite beach dubai": "Kite Beach Dubai",
        "dubai": "Kite Beach Dubai",
        
        "2": "Kite Beach Abu Dhabi", 
        "2.": "Kite Beach Abu Dhabi",
        "2. kite beach abu dhabi": "Kite Beach Abu Dhabi",
        "2.kite beach abu dhabi": "Kite Beach Abu Dhabi",
        "kite beach abu dhabi": "Kite Beach Abu Dhabi",
        "abu dhabi": "Kite Beach Abu Dhabi",
        
        "3": "Jebel Ali Kite Beach",
        "3.": "Jebel Ali Kite Beach",
        "3. jebel ali kite beach": "Jebel Ali Kite Beach",
        "3.jebel ali kite beach": "Jebel Ali Kite Beach",
        "jebel ali": "Jebel Ali Kite Beach",
        "jebel": "Jebel Ali Kite Beach",
        
        "4": "Al Hamra Kite Beach",
        "4.": "Al Hamra Kite Beach", 
        "4. al hamra kite beach": "Al Hamra Kite Beach",
        "4.al hamra kite beach": "Al Hamra Kite Beach",
        "al hamra": "Al Hamra Kite Beach",
        "ras al khaimah": "Al Hamra Kite Beach",
        
        "5": "Sunset Beach Umm Al Quwain",
        "5.": "Sunset Beach Umm Al Quwain",
        "5. sunset beach umm al quwain": "Sunset Beach Umm Al Quwain", 
        "5.sunset beach umm al quwain": "Sunset Beach Umm Al Quwain",
        "sunset beach": "Sunset Beach Umm Al Quwain",
        "umm al quwain": "Sunset Beach Umm Al Quwain",
        
        # Arabic
        "١": "Kite Beach Dubai",
        "1. كايت بيتش دبي": "Kite Beach Dubai",
        "كايت بيتش دبي": "Kite Beach Dubai",
        "دبي": "Kite Beach Dubai",
        
        "٢": "Kite Beach Abu Dhabi",
        "2. كايت بيتش أبوظبي": "Kite Beach Abu Dhabi", 
        "كايت بيتش أبوظبي": "Kite Beach Abu Dhabi",
        "أبوظبي": "Kite Beach Abu Dhabi",
        
        "٣": "Jebel Ali Kite Beach", 
        "3. جبل علي كايت بيتش": "Jebel Ali Kite Beach",
        "جبل علي": "Jebel Ali Kite Beach",
        
        "٤": "Al Hamra Kite Beach",
        "4. الحمرا كايت بيتش": "Al Hamra Kite Beach",
        "الحمرا": "Al Hamra Kite Beach",
        "رأس الخيمة": "Al Hamra Kite Beach",
        
        "٥": "Sunset Beach Umm Al Quwain",
        "5. سانسيت بيتش أم القيوين": "Sunset Beach Umm Al Quwain",
        "سانسيت بيتش": "Sunset Beach Umm Al Quwain", 
        "أم القيوين": "Sunset Beach Umm Al Quwain",
        
        # Skip keywords
        "нет": None,
        "нет, пропустить выбор локации": None,
        "❌ нет, пропустить выбор локации": None,
        "пропустить": None,
        "skip": None,
        "لا": None,
        "لا، تخطى اختيار الموقع": None,
        "❌ لا، تخطى اختيار الموقع": None,
        "تخطى": None,
        "no": None,
        "no, skip location selection": None
    }
    
    choice_lower = choice.strip().lower()
    return location_map.get(choice_lower, choice)

def should_skip_location(choice):
    skip_keywords = ["нет", "пропустить", "skip", "❌", "لا", "تخطى", "no"]
    choice_lower = choice.strip().lower()
    return any(keyword in choice_lower for keyword in skip_keywords)