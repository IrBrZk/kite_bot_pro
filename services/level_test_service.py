import logging
from typing import Dict, List
from config.constants import States

logger = logging.getLogger(__name__)

class LevelTestService:
    def __init__(self, language_manager):
        self.language_manager = language_manager
        self.user_progress: Dict[int, Dict] = {}
    
    def get_question(self, question_number: int, user_id: int) -> Dict:
        """Получить вопрос теста"""
        user_lang = self.language_manager.get_user_language(user_id)
        
        questions = {
            1: {
                'text': {
                    'ru': "🎯 **Вопрос 1/5**\n\nКак часто вы катаетесь на кайтсерфинге?",
                    'en': "🎯 **Question 1/5**\n\nHow often do you kite surf?",
                    'ar': "🎯 **السؤال 1/5**\n\nكم مرة تمارس ركوب الأمواج بالطائرة الورقية؟"
                },
                'options': {
                    'ru': ["Первый раз", "Несколько раз в год", "Регулярно", "Профессионально"],
                    'en': ["First time", "Several times a year", "Regularly", "Professionally"],
                    'ar': ["للمرة الأولى", "عدة مرات في السنة", "بانتظام", "باحترافية"]
                }
            },
            2: {
                'text': {
                    'ru': "🎯 **Вопрос 2/5**\n\nМожете ли вы управлять кайтом одной рукой?",
                    'en': "🎯 **Question 2/5**\n\nCan you control the kite with one hand?",
                    'ar': "🎯 **السؤال 2/5**\n\nهل يمكنك التحكم في الطائرة الورقية بيد واحدة؟"
                },
                'options': {
                    'ru': ["Нет", "Иногда", "Да, уверенно", "Профессионально"],
                    'en': ["No", "Sometimes", "Yes, confidently", "Professionally"],
                    'ar': ["لا", "أحيانًا", "نعم بثقة", "باحترافية"]
                }
            },
            3: {
                'text': {
                    'ru': "🎯 **Вопрос 3/5**\n\nКак вы стартуете с воды?",
                    'en': "🎯 **Question 3/5**\n\nHow do you start from the water?",
                    'ar': "🎯 **السؤال 3/5**\n\nكيف تبدأ من الماء؟"
                },
                'options': {
                    'ru': ["С помощью инструктора", "Самостоятельно с водным стартом", "Без проблем", "В любых условиях"],
                    'en': ["With instructor help", "Independently with water start", "No problem", "In any conditions"],
                    'ar': ["بمساعدة المدرب", "باستقلالية مع بداية مائية", "بدون مشكلة", "في أي ظرف"]
                }
            },
            4: {
                'text': {
                    'ru': "🎯 **Вопрос 4/5**\n\nКакие трюки вы можете выполнять?",
                    'en': "🎯 **Question 4/5**\n\nWhat tricks can you perform?",
                    'ar': "🎯 **السؤال 4/5**\n\nما الحيل التي يمكنك أداؤها؟"
                },
                'options': {
                    'ru': ["Никакие", "Простые прыжки", "Вращения", "Сложные акробатические трюки"],
                    'en': ["None", "Simple jumps", "Rotations", "Complex acrobatic tricks"],
                    'ar': ["لا شيء", "قفزات بسيطة", "دورانات", "حركات بهلوانية معقدة"]
                }
            },
            5: {
                'text': {
                    'ru': "🎯 **Вопрос 5/5**\n\nВ каких ветровых условиях вы катаетесь?",
                    'en': "🎯 **Question 5/5**\n\nIn what wind conditions do you ride?",
                    'ar': "🎯 **السؤال 5/5**\n\nفي أي ظروف رياح تركب؟"
                },
                'options': {
                    'ru': ["Только в идеальных", "Легкий-средний ветер", "Сильный ветер", "Любые условия"],
                    'en': ["Only in ideal", "Light-medium wind", "Strong wind", "Any conditions"],
                    'ar': ["فقط في الظروف المثالية", "رياح خفيفة إلى متوسطة", "رياح قوية", "أي ظروف"]
                }
            }
        }
        
        question_data = questions.get(question_number, {})
        return {
            'text': question_data['text'].get(user_lang, question_data['text']['en']),
            'options': question_data['options'].get(user_lang, question_data['options']['en'])
        }
    
    def start_test(self, user_id: int):
        """Начать тест для пользователя"""
        self.user_progress[user_id] = {
            'current_question': 1,
            'answers': [],
            'completed': False
        }
        logger.info(f"🎯 Level test started for user {user_id}")
    
    def save_answer(self, user_id: int, answer: str):
        """Сохранить ответ пользователя"""
        if user_id in self.user_progress:
            self.user_progress[user_id]['answers'].append(answer)
            self.user_progress[user_id]['current_question'] += 1
            
            # Проверяем завершение теста
            if self.user_progress[user_id]['current_question'] > 5:
                self.user_progress[user_id]['completed'] = True
    
    def get_current_question(self, user_id: int) -> int:
        """Получить текущий вопрос пользователя"""
        return self.user_progress.get(user_id, {}).get('current_question', 1)
    
    def is_test_completed(self, user_id: int) -> bool:
        """Проверить завершение теста"""
        return self.user_progress.get(user_id, {}).get('completed', False)
    
    def calculate_level(self, user_id: int) -> str:
        """Рассчитать уровень пользователя"""
        if user_id not in self.user_progress or not self.is_test_completed(user_id):
            return "unknown"
        
        answers = self.user_progress[user_id]['answers']
        score = 0
        
        # Простая логика подсчета очков
        for answer in answers:
            if answer in [0, "0"]:  # Первый вариант (новичок)
                score += 1
            elif answer in [1, "1"]:  # Второй вариант (начальный)
                score += 2
            elif answer in [2, "2"]:  # Третий вариант (средний)
                score += 3
            elif answer in [3, "3"]:  # Четвертый вариант (продвинутый)
                score += 4
        
        # Определение уровня по сумме баллов
        if score <= 8:
            return "beginner"
        elif score <= 12:
            return "intermediate"
        elif score <= 16:
            return "advanced"
        else:
            return "expert"
    
    def get_level_description(self, level: str, user_id: int) -> str:
        """Получить описание уровня"""
        user_lang = self.language_manager.get_user_language(user_id)
        
        levels = {
            'beginner': {
                'ru': "🎯 **НАЧИНАЮЩИЙ**\n\nРекомендуем начать с базового курса для уверенного старта!",
                'en': "🎯 **BEGINNER**\n\nWe recommend starting with a basic course for a confident start!",
                'ar': "🎯 **مبتدئ**\n\nنوصي بالبدء بدورة أساسية لبداية واثقة!"
            },
            'intermediate': {
                'ru': "🎯 **СРЕДНИЙ УРОВЕНЬ**\n\nОтлично! Можем работать над улучшением техники и новыми трюками!",
                'en': "🎯 **INTERMEDIATE**\n\nGreat! We can work on improving technique and new tricks!",
                'ar': "🎯 **متوسط المستوى**\n\nممتاز! يمكننا العمل على تحسين التقنية والحيل الجديدة!"
            },
            'advanced': {
                'ru': "🎯 **ПРОДВИНУТЫЙ**\n\nВпечатляет! Готовы к сложным трюкам и профессиональным техникам!",
                'en': "🎯 **ADVANCED**\n\nImpressive! Ready for complex tricks and professional techniques!",
                'ar': "🎯 **متقدم**\n\nمثير للإعجاب! جاهز للحيل المعقدة والتقنيات الاحترافية!"
            },
            'expert': {
                'ru': "🎯 **ЭКСПЕРТ**\n\nПрофессионал! Можем работать над соревновательными элементами!",
                'en': "🎯 **EXPERT**\n\nProfessional! We can work on competitive elements!",
                'ar': "🎯 **خبير**\n\nمحترف! يمكننا العمل على العناصر التنافسية!"
            }
        }
        
        return levels.get(level, levels['beginner']).get(user_lang, levels['beginner']['en'])

# Создаем глобальный экземпляр
from services.language_manager import language_manager
level_test_service = LevelTestService(language_manager)
