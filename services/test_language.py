# test_language.py
#!/usr/bin/env python3
from services.database_service import DatabaseService
from services.language_manager import LanguageManager

def test_language_saving():
    database_service = DatabaseService()
    language_manager = LanguageManager()
    
    test_user_id = 224853932
    
    # Проверяем текущий язык
    current_lang = language_manager.get_user_language(test_user_id)
    print(f"Текущий язык пользователя {test_user_id}: {current_lang}")
    
    # Меняем язык
    database_service.set_user_language(test_user_id, 'ar')
    language_manager.set_user_language(test_user_id, 'ar')
    
    # Проверяем снова
    new_lang = language_manager.get_user_language(test_user_id)
    print(f"Новый язык пользователя {test_user_id}: {new_lang}")
    
    # Проверяем сохранение в файл
    database_service.save_users()
    print("✅ Данные сохранены")

if __name__ == '__main__':
    test_language_saving()