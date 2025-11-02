from services.language_manager import language_manager

class SafetyService:
    @staticmethod
    def get_safety_rules(user_id: int) -> str:
        """Получить правила безопасности на языке пользователя"""
        user_lang = language_manager.get_user_language(user_id)
        
        if user_lang == 'ru':
            return SafetyService._get_russian_rules()
        elif user_lang == 'ar':
            return SafetyService._get_arabic_rules()
        else:
            return SafetyService._get_english_rules()
    
    @staticmethod
    def _get_russian_rules() -> str:
        """Русская версия правил безопасности"""
        rules = [
            "✅ **Обязательная экипировка:**\n- Шлем\n- Спасжилет\n- Трапеция\n- Лиш (страховочная система)",
            "✅ **Проверка оборудования:**\n- Осмотр кайта перед запуском\n- Проверка строп\n- Тест систем безопасности", 
            "✅ **Оценка условий:**\n- Сила и направление ветра\n- Течения и волны\n- Наличие других райдеров",
            "✅ **Сигналы и коммуникация:**\n- Сигналы инструктора\n- Жесты для общения на воде\n- Система партнерства",
            "✅ **Экстренные ситуации:**\n- Отстрел кайта\n- Потеря доски\n- Помощь другим райдерам"
        ]
        
        title = "🛟 **ПРАВИЛА БЕЗОПАСНОСТИ КАЙТСЕРФИНГА**"
        important = "💡 **Важно:** Безопасность - наш приоритет! Все занятия проводятся под контролем опытного инструктора."
        
        rules_text = "\n\n".join(rules)
        return f"{title}\n\n{rules_text}\n\n{important}"
    
    @staticmethod
    def _get_english_rules() -> str:
        """Английская версия правил безопасности"""
        rules = [
            "✅ **Mandatory equipment:**\n- Helmet\n- Life jacket\n- Harness\n- Leash (safety system)",
            "✅ **Equipment check:**\n- Kite inspection before launch\n- Line check\n- Safety system test", 
            "✅ **Conditions assessment:**\n- Wind strength and direction\n- Currents and waves\n- Presence of other riders",
            "✅ **Signals and communication:**\n- Instructor signals\n- Gestures for water communication\n- Buddy system",
            "✅ **Emergency situations:**\n- Kite release\n- Board loss\n- Helping other riders"
        ]
        
        title = "🛟 **KITESURFING SAFETY RULES**"
        important = "💡 **Important:** Safety is our priority! All lessons are conducted under the supervision of an experienced instructor."
        
        rules_text = "\n\n".join(rules)
        return f"{title}\n\n{rules_text}\n\n{important}"
    
    @staticmethod
    def _get_arabic_rules() -> str:
        """Арабская версия правил безопасности"""
        rules = [
            "✅ **المعدات الإلزامية:**\n- خوذة\n- سترة نجاة\n- حزام\n- حبل الأمان",
            "✅ **فحص المعدات:**\n- فحص الطائرة قبل الإطلاق\n- فحص الحبال\n- اختبار أنظمة السلامة", 
            "✅ **تقييم الظروف:**\n- قوة واتجاه الرياح\n- التيارات والأمواج\n- وجود راكبين آخرين",
            "✅ **الإشارات والاتصال:**\n- إشارات المدرب\n- إيماءات للتواصل في الماء\n- نظام الزميل",
            "✅ **حالات الطوارئ:**\n- إطلاق الطائرة\n- فقدان اللوح\n- مساعدة المتزلجين الآخرين"
        ]
        
        title = "🛟 **قواعد السلامة في ركوب الأمواج الشراعي**"
        important = "💡 **مهم:** السلامة هي أولويتنا! جميع الدروس تجري تحت إشراف مدرب ذو خبرة."
        
        rules_text = "\n\n".join(rules)
        return f"{title}\n\n{rules_text}\n\n{important}"

# Глобальный экземпляр
safety_service = SafetyService()