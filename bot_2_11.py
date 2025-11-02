#!/usr/bin/env python3
"""
Главный файл бота для кайтсерфинга
"""
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler

from config.settings import TELEGRAM_BOT_TOKEN
from config.constants import States
from handlers.menu_handlers import *
from handlers.booking_handlers import *
from handlers.level_test_handlers import *

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Точка входа в приложение"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
        return
    
    try:
        # Создаем приложение
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Обработчик диалога бронирования
        booking_conv_handler = ConversationHandler(
            entry_points=[
                MessageHandler(filters.TEXT & filters.Regex('^(🎯 Забронировать занятие|🎯 Book|🎯 حجز)$'), start_booking)
            ],
            states={
                States.BOOKING_DATE: [
                    CallbackQueryHandler(handle_calendar_callback, pattern='^(book_date_|cancel_booking)')
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
        
        # Обработчик теста уровня
        level_test_conv_handler = ConversationHandler(
            entry_points=[
                MessageHandler(filters.TEXT & filters.Regex('^(📊 Тест уровня|📊 Level Test|📊 اختبار المستوى)$'), start_level_test)
            ],
            states={
                States.LEVEL_TEST: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_level_test_answer)
                ]
            },
            fallbacks=[
                MessageHandler(filters.TEXT & filters.Regex('^(⬅️ Назад|⬅️ Back|⬅️ عودة)$'), handle_level_test_back)
            ]
        )
        
        # Основные обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(booking_conv_handler)
        application.add_handler(level_test_conv_handler)
        
        # Обработчики меню
        application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^(📍 Локации для катания|📍 Locations|📍 المواقع)$'), handle_locations))
        application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^(🛟 Правила безопасности|🛟 Safety Rules|🛟 قواعد السلامة)$'), handle_safety))
        application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^(📞 Контакты Абдулы|📞 Contacts|📞 جهات الاتصال)$'), handle_contacts))
        application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^(📸 Галерея и отзывы|📸 Gallery|📸 المعرض)$'), handle_gallery))
        application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^(🌐 Сменить язык|🌐 Change Language|🌐 تغيير اللغة)$'), handle_language_selection))
        application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^🛠️ Админ-панель$'), handle_admin_panel))
        
        # Общий обработчик текста
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu))
        
        # Запускаем бота
        logger.info("🤖 Бот запущен и готов к работе!")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise

if __name__ == '__main__':
    main()