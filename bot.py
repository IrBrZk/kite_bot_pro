#!/usr/bin/env python3
# bot.py - упрощенная версия без сложного asyncio
import logging
import asyncio
from telegram.ext import Application, CommandHandler, ConversationHandler

# Импорт конфигурации
from config.settings import TELEGRAM_BOT_TOKEN
from config.constants import States

# Импорт сервисов
from services.language_manager import LanguageManager
from services.database_service import DatabaseService
from services.booking_service import BookingService
from services.gallery_service import GalleryService
from services.level_test_service import LevelTestService
from services.admin_service import AdminService
from services.calendar_service import CalendarService
from services.safety_service import SafetyService

# Импорт хендлеров
from handlers.menu_handlers import MenuHandlers
from handlers.booking_handlers import BookingHandlers
from handlers.gallery_handlers import GalleryHandlers
from handlers.level_test_handlers import LevelTestHandlers
from handlers.admin_handlers import AdminHandlers

# Импорт роутера
from router.handlers_router import HandlersRouter

# Утилиты
from utils.keyboards import KeyboardManager

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class BotManager:
    def __init__(self):
        logger.info("🔄 Инициализация BotManager...")
        
        # Инициализация основных сервисов
        self.database_service = DatabaseService()
        self.language_manager = LanguageManager()
        
        # Бизнес-сервисы
        self.booking_service = BookingService(self.database_service)
        self.calendar_service = CalendarService(self.booking_service)
        self.gallery_service = GalleryService(self.language_manager)
        self.level_test_service = LevelTestService(self.language_manager)
        self.safety_service = SafetyService(self.language_manager)
        self.admin_service = AdminService(
            self.booking_service, self.gallery_service, 
            self.database_service, self.language_manager
        )
        
        # KeyboardManager должен быть после booking_service
        self.keyboard_manager = KeyboardManager(self.language_manager, self.booking_service)
        
        # Инициализация хендлеров
        self.menu_handlers = MenuHandlers(
            self.language_manager, self.database_service, self.keyboard_manager
        )
        self.booking_handlers = BookingHandlers(
            self.language_manager, self.database_service, self.keyboard_manager,
            self.booking_service, self.calendar_service
        )
        self.gallery_handlers = GalleryHandlers(
            self.language_manager, self.database_service, self.keyboard_manager,
            self.gallery_service
        )
        self.level_test_handlers = LevelTestHandlers(
            self.language_manager, self.database_service, self.keyboard_manager,
            self.level_test_service
        )
        self.admin_handlers = AdminHandlers(
            self.language_manager, self.database_service, self.keyboard_manager,
            self.admin_service
        )
        
        # Роутер
        self.router = HandlersRouter(
            self.menu_handlers, self.booking_handlers, self.gallery_handlers,
            self.level_test_handlers, self.admin_handlers
        )
    
    async def setup(self):
        """Настройка бота"""
        logger.info("🔄 Настройка сервисов...")
        await self.database_service.init_db()
        logger.info("✅ Сервисы настроены")
    
    def create_application(self):
        """Создание приложения с обработчиками"""
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Основной ConversationHandler от роутера
        conversation_handler = self.router.create_conversation_handler()
        application.add_handler(conversation_handler)
        
        # Отдельные админ-команды
        application.add_handler(CommandHandler('admin', self.admin_handlers.handle_admin_command))
        
        # Обработчик ошибок
        application.add_error_handler(self.error_handler)
        
        logger.info("✅ Обработчики добавлены")
        return application
    
    async def error_handler(self, update, context):
        """Обработчик ошибок"""
        logger.error(f"❌ Ошибка: {context.error}", exc_info=context.error)

def main():
    """Основная функция запуска - упрощенная версия"""
    try:
        # Создаем новый event loop для текущего потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        bot_manager = BotManager()
        
        # Запускаем настройку в event loop
        loop.run_until_complete(bot_manager.setup())
        
        application = bot_manager.create_application()
        
        logger.info("🚀 Kite Bot Pro запущен!")
        
        # Запускаем polling
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка запуска: {e}")
        raise

if __name__ == '__main__':
    main()
EOFcat > /opt/kite_bot_pro/bot.py << 'EOF'
#!/usr/bin/env python3
# bot.py - упрощенная версия без сложного asyncio
import logging
import asyncio
from telegram.ext import Application, CommandHandler, ConversationHandler

# Импорт конфигурации
from config.settings import TELEGRAM_BOT_TOKEN
from config.constants import States

# Импорт сервисов
from services.language_manager import LanguageManager
from services.database_service import DatabaseService
from services.booking_service import BookingService
from services.gallery_service import GalleryService
from services.level_test_service import LevelTestService
from services.admin_service import AdminService
from services.calendar_service import CalendarService
from services.safety_service import SafetyService

# Импорт хендлеров
from handlers.menu_handlers import MenuHandlers
from handlers.booking_handlers import BookingHandlers
from handlers.gallery_handlers import GalleryHandlers
from handlers.level_test_handlers import LevelTestHandlers
from handlers.admin_handlers import AdminHandlers

# Импорт роутера
from router.handlers_router import HandlersRouter

# Утилиты
from utils.keyboards import KeyboardManager

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class BotManager:
    def __init__(self):
        logger.info("🔄 Инициализация BotManager...")
        
        # Инициализация основных сервисов
        self.database_service = DatabaseService()
        self.language_manager = LanguageManager()
        
        # Бизнес-сервисы
        self.booking_service = BookingService(self.database_service)
        self.calendar_service = CalendarService(self.booking_service)
        self.gallery_service = GalleryService(self.language_manager)
        self.level_test_service = LevelTestService(self.language_manager)
        self.safety_service = SafetyService(self.language_manager)
        self.admin_service = AdminService(
            self.booking_service, self.gallery_service, 
            self.database_service, self.language_manager
        )
        
        # KeyboardManager должен быть после booking_service
        self.keyboard_manager = KeyboardManager(self.language_manager, self.booking_service)
        
        # Инициализация хендлеров
        self.menu_handlers = MenuHandlers(
            self.language_manager, self.database_service, self.keyboard_manager
        )
        self.booking_handlers = BookingHandlers(
            self.language_manager, self.database_service, self.keyboard_manager,
            self.booking_service, self.calendar_service
        )
        self.gallery_handlers = GalleryHandlers(
            self.language_manager, self.database_service, self.keyboard_manager,
            self.gallery_service
        )
        self.level_test_handlers = LevelTestHandlers(
            self.language_manager, self.database_service, self.keyboard_manager,
            self.level_test_service
        )
        self.admin_handlers = AdminHandlers(
            self.language_manager, self.database_service, self.keyboard_manager,
            self.admin_service
        )
        
        # Роутер
        self.router = HandlersRouter(
            self.menu_handlers, self.booking_handlers, self.gallery_handlers,
            self.level_test_handlers, self.admin_handlers
        )
    
    async def setup(self):
        """Настройка бота"""
        logger.info("🔄 Настройка сервисов...")
        await self.database_service.init_db()
        logger.info("✅ Сервисы настроены")
    
    def create_application(self):
        """Создание приложения с обработчиками"""
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Основной ConversationHandler от роутера
        conversation_handler = self.router.create_conversation_handler()
        application.add_handler(conversation_handler)
        
        # Отдельные админ-команды
        application.add_handler(CommandHandler('admin', self.admin_handlers.handle_admin_command))
        
        # Обработчик ошибок
        application.add_error_handler(self.error_handler)
        
        logger.info("✅ Обработчики добавлены")
        return application
    
    async def error_handler(self, update, context):
        """Обработчик ошибок"""
        logger.error(f"❌ Ошибка: {context.error}", exc_info=context.error)

def main():
    """Основная функция запуска - упрощенная версия"""
    try:
        # Создаем новый event loop для текущего потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        bot_manager = BotManager()
        
        # Запускаем настройку в event loop
        loop.run_until_complete(bot_manager.setup())
        
        application = bot_manager.create_application()
        
        logger.info("🚀 Kite Bot Pro запущен!")
        
        # Запускаем polling
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка запуска: {e}")
        raise

if __name__ == '__main__':
    main()
