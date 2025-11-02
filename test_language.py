#!/usr/bin/env python3
from services.language_manager import language_manager

def test_current_state():
    user_id = 224853932
    
    print("🧪 ТЕСТ LANGUAGE MANAGER")
    print(f"User ID: {user_id}")
    
    # Проверяем текущий язык
    current_lang = language_manager.get_user_language(user_id)
    print(f"Текущий язык: {current_lang}")
    
    # Устанавливаем русский (как в логах)
    language_manager.set_user_language(user_id, 'ru')
    
    # Проверяем тексты
    print(f"Приветствие: {language_manager.get_text(user_id, 'welcome', first_name='Test')}")
    print(f"Меню бронирования: {language_manager.get_text(user_id, 'menu_booking')}")
    print(f"Меню домой: {language_manager.get_text(user_id, 'menu_home')}")
    
    # Проверяем все тексты меню
    menu_texts = language_manager.get_all_menu_texts(user_id)
    print(f"Все тексты меню: {menu_texts}")

if __name__ == '__main__':
    test_current_state()
