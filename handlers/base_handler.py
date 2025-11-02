# Базовый класс для обработчиков (упрощенная версия)
class BaseHandler:
    def __init__(self, language_manager, database_service, keyboard_manager):
        self.language_manager = language_manager
        self.database_service = database_service
        self.keyboard_manager = keyboard_manager
