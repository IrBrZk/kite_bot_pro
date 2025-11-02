# services/calendar_service.py
import logging
from datetime import datetime, timedelta
from typing import List, Dict
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

class CalendarService:
    def __init__(self, booking_service):
        self.booking_service = booking_service
    
    def generate_calendar(self, year: int = None, month: int = None) -> Dict:
        """Сгенерировать календарь на месяц"""
        now = datetime.now()
        if not year:
            year = now.year
        if not month:
            month = now.month
        
        # Первый день месяца
        first_day = datetime(year, month, 1)
        # Последний день месяца
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)
        
        # Дни недели первого дня
        start_weekday = first_day.weekday()
        
        # Генерация календаря
        calendar_days = []
        current_date = first_day - timedelta(days=start_weekday)
        
        # 6 недель максимум
        for week in range(6):
            week_days = []
            for day in range(7):
                week_days.append({
                    'date': current_date.date(),
                    'is_current_month': current_date.month == month,
                    'is_past': current_date.date() < now.date(),
                    'is_today': current_date.date() == now.date()
                })
                current_date += timedelta(days=1)
            
            # Если вышли за пределы месяца и неделя пустая, останавливаемся
            if week > 3 and all(not day['is_current_month'] for day in week_days):
                break
                
            calendar_days.append(week_days)
        
        return {
            'year': year,
            'month': month,
            'month_name': first_day.strftime('%B %Y'),
            'days': calendar_days
        }
    
    def get_calendar_keyboard(self, year: int = None, month: int = None) -> InlineKeyboardMarkup:
        """Создать клавиатуру календаря"""
        calendar_data = self.generate_calendar(year, month)
        
        keyboard = []
        
        # Заголовок с навигацией
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        
        header_buttons = [
            InlineKeyboardButton("◀️", callback_data=f"calendar_{prev_year}_{prev_month}"),
            InlineKeyboardButton(calendar_data['month_name'], callback_data="calendar_current"),
            InlineKeyboardButton("▶️", callback_data=f"calendar_{next_year}_{next_month}")
        ]
        keyboard.append(header_buttons)
        
        # Дни недели
        week_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        keyboard.append([InlineKeyboardButton(day, callback_data="ignore") for day in week_days])
        
        # Дни месяца
        for week in calendar_data['days']:
            week_buttons = []
            for day_data in week:
                date_str = day_data['date'].strftime("%Y-%m-%d")
                day_num = day_data['date'].day
                
                if not day_data['is_current_month']:
                    # Дни другого месяца
                    week_buttons.append(InlineKeyboardButton(" ", callback_data="ignore"))
                elif day_data['is_past']:
                    # Прошедшие дни
                    week_buttons.append(InlineKeyboardButton(f"❌", callback_data="ignore"))
                else:
                    # Доступные дни
                    week_buttons.append(InlineKeyboardButton(
                        f"📅{day_num}" if day_data['is_today'] else str(day_num),
                        callback_data=f"book_date_{date_str}"
                    ))
            keyboard.append(week_buttons)
        
        # Кнопка отмены
        keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_booking")])
        
        return InlineKeyboardMarkup(keyboard)
    
    def is_date_available(self, date: str) -> bool:
        """Проверить доступность даты"""
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
            today = datetime.now().date()
            return target_date >= today
        except ValueError:
            return False
    
    def get_available_time_slots(self, date: str) -> List[str]:
        """Получить доступные временные слоты для даты"""
        # Здесь можно добавить логику проверки занятых слотов
        # Пока возвращаем все стандартные слоты
        return [
            "07:00", "08:00", "09:00", "10:00", "11:00", "12:00",
            "13:00", "14:00", "15:00", "16:00", "17:00", "18:00"
        ]