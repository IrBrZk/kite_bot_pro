#!/usr/bin/env python3
# modern_bot.py - полная версия бота с обновленными сервисами
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

from config.settings import TELEGRAM_BOT_TOKEN, LOCATIONS, SCHEDULE, CONTACTS
from config.constants import States
from services import language_manager, database_service

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Простые функции клавиатур
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
        await update.message.reply_text("📅 Функция бронирования скоро будет доступна!")
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
        
        # Сохраняем в базу через новый метод
        await database_service.update_user(user_id, language=language_code, language_selected=True)
        
        confirmation = language_manager.get_text(user_id, 'language.changed')
        await update.message.reply_text(
            confirmation,
            reply_markup=get_main_menu(user_id)
        )
        
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
    
    await update.message.reply_text(
        contacts_text,
        parse_mode='Markdown',
        reply_markup=get_main_menu(user_id)
    )

async def handle_locations(update, context):
    """Обработчик локаций"""
    user_id = update.effective_user.id
    user_lang = language_manager.get_user_language(user_id)
    
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
    logger.info("🚀 Modern Kite Bot запускается...")
    
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Инициализация базы данных
    loop.run_until_complete(database_service.init_db())
    
    # Создание приложения
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Conversation Handler для управления состояниями
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
    
    logger.info("✅ Modern Bot запущен и готов к работе!")
    application.run_polling()

if __name__ == '__main__':
    main()
