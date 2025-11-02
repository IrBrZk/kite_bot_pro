# router/handlers_router.py
from telegram.ext import ConversationHandler, MessageHandler, filters, CommandHandler, CallbackQueryHandler
from config.constants import States

class HandlersRouter:
    def __init__(self, menu_handlers, booking_handlers, gallery_handlers, level_test_handlers, admin_handlers):
        self.menu_handlers = menu_handlers
        self.booking_handlers = booking_handlers
        self.gallery_handlers = gallery_handlers
        self.level_test_handlers = level_test_handlers
        self.admin_handlers = admin_handlers
    
    def create_conversation_handler(self):
        return ConversationHandler(
            entry_points=[CommandHandler('start', self.menu_handlers.start)],
            states={
                States.START: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.menu_handlers.show_main_menu)
                ],
                States.MAIN_MENU: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.route_main_menu)
                ],
                States.LANGUAGE_SELECTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.menu_handlers.change_language)
                ],
                States.GALLERY_VIEW: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.gallery_handlers.handle_gallery_actions),
                    CallbackQueryHandler(self.gallery_handlers.handle_gallery_pagination, pattern="^gallery_")
                ],
                States.BOOKING_DATE: [
                    CallbackQueryHandler(self.booking_handlers.handle_calendar_callback, pattern="^(calendar_|book_date_|cancel_booking)")
                ],
                States.BOOKING_TIME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.booking_handlers.handle_time_selection)
                ],
                States.BOOKING_LOCATION_CHOICE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.booking_handlers.handle_location_selection)
                ],
                States.BOOKING_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.booking_handlers.handle_name_input)
                ],
                States.BOOKING_CONFIRM: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.booking_handlers.handle_booking_confirmation)
                ],
                States.LEVEL_TEST_Q1: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, 
                        lambda u, c: self.level_test_handlers.handle_answer(u, c, 1))
                ],
                # ... остальные состояния теста
                States.SAFETY: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.menu_handlers.show_main_menu)
                ]
            },
            fallbacks=[CommandHandler('cancel', self.menu_handlers.cancel)]
        )
    
    async def route_main_menu(self, update, context):
        user_id = update.effective_user.id
        text = update.message.text
        
        # Получаем тексты меню через LanguageManager (не через хендлеры)
        menu_texts = self.menu_handlers.language_manager.get_all_menu_texts(user_id)
        
        if text == menu_texts['booking']:
            return await self.booking_handlers.start_booking(update, context)
        elif text == menu_texts['level_test']:
            return await self.level_test_handlers.start_level_test(update, context)
        elif text == menu_texts['gallery']:
            return await self.gallery_handlers.start_gallery(update, context)
        elif text == menu_texts['safety']:
            return await self.menu_handlers.handle_safety(update, context)
        elif text == menu_texts['language']:
            return await self.menu_handlers.handle_language_selection(update, context)
        elif text == menu_texts['contacts']:
            return await self.menu_handlers.handle_contacts(update, context)
        elif text == menu_texts['locations']:
            return await self.menu_handlers.handle_locations(update, context)
        else:
            return await self.menu_handlers.show_main_menu(update, context)