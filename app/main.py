#!/usr/bin/env python3
import logging
import asyncio
from telegram.ext import Application, CommandHandler
from app.container import create_container
from handlers.commands import start_handler, help_handler
from handlers.errors import error_handler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger('telegram').setLevel(logging.INFO)

def build_app():
    container = create_container()
    app = Application.builder().token(container.config.TELEGRAM_TOKEN).build()
    app.container = container

    # Register handlers (only registrations, no business logic here)
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_error_handler(error_handler)

    return app

def main():
    app = build_app()
    logger.info("Starting bot (scaffold)")
    app.run_polling()

if __name__ == "__main__":
    main()
