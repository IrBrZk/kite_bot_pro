#!/usr/bin/env python3
# simple_final_bot.py - рабочая версия без asyncio проблем
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from telegram import ReplyKeyboardMarkup, KeyboardButton

from config.settings import TELEGRAM_BOT_TOKEN
from config.constants import States
from services.language_manager import LanguageManager
from services.database_service import DatabaseService

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Глобальные сервисы
language_manager = LanguageManager()
database_service = DatabaseService()

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
        await update.message.reply_text("📅 Функция бронирования скоро будет доступна!")
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

async def handle_language_selection(update, context):
    """Обработка выбора языка"""
    user_id = update.effective_user.id
    text = update.message.text
    
    # Определяем язык по тексту кнопки
    language_map = {
        'English 🇺🇸': 'en',
        'Russian 🇷🇺': 'ru', 
        'Arabic 🇦🇪': 'ar'
    }
    
    language_code = language_map.get(text, 'en')
    
    # Сохраняем язык пользователя
    language_manager.set_user_language(user_id, language_code)
    
    # Обновляем пользователя в БД
    user = await database_service.get_user(user_id)
    if user:
        user.language = language_code
        user.language_selected = True
        await database_service.update_user(user)
    
    # Подтверждение смены языка
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
    await update.message.reply_text(
        "Операция отменена",
        reply_markup=get_main_menu(user_id)
    )
    return ConversationHandler.END

async def error_handler(update, context):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")

def main():
    """Основная функция запуска"""
    logger.info("🚀 Kite Bot Pro запускается...")
    
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
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    
    logger.info("✅ Бот запущен и готов к работе!")
    application.run_polling()

if __name__ == '__main__':
    main()
