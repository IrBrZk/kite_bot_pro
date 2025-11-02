#!/usr/bin/env python3
"""
Упрощенная версия бота для тестирования
"""
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from config.settings import TELEGRAM_BOT_TOKEN
from services.language_manager import language_manager
from services.database_service import database_service
from utils.keyboards import get_main_menu, get_language_keyboard

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update, context):
    """Обработчик команды /start"""
    user = update.effective_user
    user_id = user.id
    logger.info(f"👋 User: {user_id} - {user.first_name}")

    user_obj = await database_service.get_user(user_id)
    if not user_obj:
        user_obj = await database_service.create_user(user)
    
    welcome_text = f"🎉 Добро пожаловать, {user.first_name}! Готовы покорять волны?"
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu(user_id),
        parse_mode='Markdown'
    )

async def handle_main_menu(update, context):
    """Обработчик главного меню"""
    user_id = update.effective_user.id
    text = update.message.text
    
    if text == "🌐 Сменить язык":
        await update.message.reply_text("🌐 Выберите язык:", reply_markup=get_language_keyboard())
    elif text == "🛟 Правила безопасности":
        from services.safety_service import safety_service
        safety_text = safety_service.get_safety_content(user_id)
        await update.message.reply_text(safety_text, parse_mode='Markdown', reply_markup=get_main_menu(user_id))
    elif text == "📊 Тест уровня":
        await update.message.reply_text("🎯 Тест уровня скоро будет доступен!", reply_markup=get_main_menu(user_id))
    elif text == "📍 Локации для катания":
        await update.message.reply_text("📍 Локации скоро будут доступны!", reply_markup=get_main_menu(user_id))
    elif text == "📞 Контакты Абдулы":
        await update.message.reply_text("📞 Контакты скоро будут доступны!", reply_markup=get_main_menu(user_id))
    elif text == "📸 Галерея и отзывы":
        await update.message.reply_text("📸 Галерея скоро будет доступна!", reply_markup=get_main_menu(user_id))
    else:
        await update.message.reply_text("❌ Неизвестная команда")

async def handle_language_selection(update, context):
    """Обработчик выбора языка"""
    user_id = update.effective_user.id
    text = update.message.text
    
    language_map = {'English 🇺🇸': 'en', 'Russian 🇷🇺': 'ru', 'Arabic 🇦🇪': 'ar'}
    language_code = language_map.get(text, 'en')
    
    language_manager.set_user_language(user_id, language_code)
    user = await database_service.get_user(user_id)
    if user:
        user.language = language_code
        await database_service.update_user(user)
    
    if language_code == 'ru': 
        confirmation = "✅ Язык изменен на русский"
    elif language_code == 'ar': 
        confirmation = "✅ تم تغيير اللغة إلى العربية"
    else: 
        confirmation = "✅ Language changed to English"
    
    await update.message.reply_text(confirmation, reply_markup=get_main_menu(user_id))

def main():
    """Точка входа в приложение"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
        return
    
    try:
        # Создаем приложение
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Основные обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^(🌐 Сменить язык|🌐 Change Language|🌐 تغيير اللغة)$'), handle_language_selection))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu))
        
        # Запускаем бота
        logger.info("🤖 Бот запущен и готов к работе!")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise

if __name__ == '__main__':
    main()
