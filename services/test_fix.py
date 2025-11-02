# test_fix.py
#!/usr/bin/env python3
from services.language_manager import language_manager

def test_language():
    test_user_id = 224853932
    
    print("🧪 Testing Language Manager...")
    
    # Тестируем установку языка
    print(f"Initial language: {language_manager.get_user_language(test_user_id)}")
    
    language_manager.set_user_language(test_user_id, 'ru')
    print(f"After setting Russian: {language_manager.get_user_language(test_user_id)}")
    print(f"Russian text: {language_manager.get_text(test_user_id, 'menu_booking')}")
    
    language_manager.set_user_language(test_user_id, 'ar')
    print(f"After setting Arabic: {language_manager.get_user_language(test_user_id)}")
    print(f"Arabic text: {language_manager.get_text(test_user_id, 'menu_booking')}")
    
    language_manager.set_user_language(test_user_id, 'en')
    print(f"After setting English: {language_manager.get_user_language(test_user_id)}")
    print(f"English text: {language_manager.get_text(test_user_id, 'menu_booking')}")

if __name__ == '__main__':
    test_language()