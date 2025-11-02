import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from config.constants import States
from services.level_test_service import level_test_service
from services.database_service import database_service
from utils.keyboards import get_main_menu, get_level_test_keyboard, get_back_keyboard

logger = logging.getLogger(__name__)

async def start_level_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать тест уровня"""
    user_id = update.effective_user.id
    
    # Начинаем тест
    level_test_service.start_test(user_id)
    
    # Получаем первый вопрос
    question_data = level_test_service.get_question(1, user_id)
    
    if question_data:
        await update.message.reply_text(
            question_data['text'],
            reply_markup=get_level_test_keyboard(0, user_id),
            parse_mode='Markdown'
        )
        return States.LEVEL_TEST
    
    await update.message.reply_text("❌ Ошибка запуска теста", reply_markup=get_main_menu(user_id))
    return States.MAIN_MENU

async def handle_level_test_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ответа на вопрос теста"""
    user_id = update.effective_user.id
    answer_text = update.message.text
    
    # Получаем текущий вопрос
    current_question = level_test_service.get_current_question(user_id)
    
    # Определяем выбранный вариант (A, B, C, D)
    selected_option = None
    question_data = level_test_service.get_question(current_question, user_id)
    
    if question_data:
        for option_key, option_text in question_data['options'].items():
            if answer_text == option_text:
                selected_option = option_key
                break
    
    if selected_option:
        # Сохраняем ответ
        level_test_service.save_answer(user_id, selected_option)
        
        # Проверяем, завершен ли тест
        if level_test_service.is_test_completed(user_id):
            # Рассчитываем уровень
            level = level_test_service.calculate_level(user_id)
            level_description = level_test_service.get_level_description(level, user_id)
            
            # Сохраняем уровень пользователя
            await database_service.update_user_level(user_id, level)
            
            await update.message.reply_text(
                level_description,
                reply_markup=get_main_menu(user_id),
                parse_mode='Markdown'
            )
            return States.MAIN_MENU
        else:
            # Показываем следующий вопрос
            next_question = level_test_service.get_current_question(user_id)
            question_data = level_test_service.get_question(next_question, user_id)
            
            if question_data:
                await update.message.reply_text(
                    question_data['text'],
                    reply_markup=get_level_test_keyboard(next_question - 1, user_id),
                    parse_mode='Markdown'
                )
                return States.LEVEL_TEST
    
    # Если ответ не распознан, показываем текущий вопрос снова
    current_question = level_test_service.get_current_question(user_id)
    question_data = level_test_service.get_question(current_question, user_id)
    
    if question_data:
        await update.message.reply_text(
            "❌ Пожалуйста, выберите вариант из предложенных:\n\n" + question_data['text'],
            reply_markup=get_level_test_keyboard(current_question - 1, user_id),
            parse_mode='Markdown'
        )
    
    return States.LEVEL_TEST

async def handle_level_test_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выход из теста уровня"""
    user_id = update.effective_user.id
    
    # Очищаем прогресс теста
    if user_id in level_test_service.user_progress:
        del level_test_service.user_progress[user_id]
    
    await update.message.reply_text(
        "❌ Тест уровня отменен",
        reply_markup=get_main_menu(user_id)
    )
    return States.MAIN_MENU