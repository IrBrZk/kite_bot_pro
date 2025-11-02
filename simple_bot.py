#!/usr/bin/env python3
# simple_bot.py - простейший запуск
import logging
from telegram.ext import Application
from config.settings import TELEGRAM_BOT_TOKEN

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    # Просто создаем приложение и запускаем
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    logger = logging.getLogger(__name__)
    logger.info("🤖 Kite Bot Pro запускается...")
    
    application.run_polling()

if __name__ == '__main__':
    main()
