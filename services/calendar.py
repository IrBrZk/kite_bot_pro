# services/calendar.py
import logging
import sqlite3
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

class Calendar:
    def __init__(self, database):
        self.db = database
    
    def get_booked_slots(self, date):
        """Получить занятые слоты на дату"""
        try:
            with sqlite3.connect('kite_bot.db') as conn:
                cursor = conn.execute(
                    'SELECT time FROM schedule_slots WHERE date = ? AND status IN ("booked", "confirmed")',
                    (date,)
                )
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting booked slots: {e}")
            return []
    
    def generate_calendar(self, year=None, month=None):
        now = datetime.now()
        if not year:
            year = now.year
        if not month:
            month = now.month
        
        month_names = {
            1: "January", 2: "February", 3: "March", 4: "April",
            5: "May", 6: "June", 7: "July", 8: "August", 
            9: "September", 10: "October", 11: "November", 12: "December"
        }
        
        keyboard = []
        
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        
        header_row = [
            InlineKeyboardButton("◀️", callback_data=f"cal_prev_{prev_year}_{prev_month}"),
            InlineKeyboardButton(f"{month_names[month]} {year}", callback_data=f"cal_header_{year}_{month}"),
            InlineKeyboardButton("▶️", callback_data=f"cal_next_{next_year}_{next_month}")
        ]
        keyboard.append(header_row)
        
        days_row = [
            InlineKeyboardButton("Mon", callback_data="cal_ignore_1"),
            InlineKeyboardButton("Tue", callback_data="cal_ignore_2"),
            InlineKeyboardButton("Wed", callback_data="cal_ignore_3"),
            InlineKeyboardButton("Thu", callback_data="cal_ignore_4"),
            InlineKeyboardButton("Fri", callback_data="cal_ignore_5"),
            InlineKeyboardButton("Sat", callback_data="cal_ignore_6"),
            InlineKeyboardButton("Sun", callback_data="cal_ignore_7")
        ]
        keyboard.append(days_row)
        
        first_day = datetime(year, month, 1)
        last_day = datetime(year, month + 1, 1) - timedelta(days=1) if month < 12 else datetime(year + 1, 1, 1) - timedelta(days=1)
        
        current_date = first_day - timedelta(days=first_day.weekday())
        cell_counter = 0
        
        while current_date <= last_day or len(keyboard) < 7:
            week_row = []
            for _ in range(7):
                cell_counter += 1
                if current_date.month == month and current_date >= now.replace(hour=0, minute=0, second=0, microsecond=0):
                    day_text = str(current_date.day)
                    callback_data = f"cal_day_{current_date.strftime('%Y_%m_%d')}"
                    week_row.append(InlineKeyboardButton(day_text, callback_data=callback_data))
                else:
                    week_row.append(InlineKeyboardButton(" ", callback_data=f"cal_empty_{cell_counter}"))
                current_date += timedelta(days=1)
            keyboard.append(week_row)
        
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cal_cancel")])
        return InlineKeyboardMarkup(keyboard)
    
    def get_available_time_slots(self, date, selected_times=None):
        """Получить доступные временные слоты с учетом занятых"""
        time_slots = [
            "07:00", "08:00", "09:00", "10:00", "11:00", "12:00",
            "13:00", "14:00", "15:00", "16:00", "17:00", "18:00"
        ]
        
        if selected_times is None:
            selected_times = []
        
        # Получаем занятые слоты
        booked_slots = self.get_booked_slots(date)
        
        available_slots = []
        for time_slot in time_slots:
            if time_slot in booked_slots:
                # Занятый слот - серый и неактивный
                button_text = f"❌ {time_slot}"
                callback_data = "time_booked"
            elif time_slot in selected_times:
                # Выбранный пользователем слот
                button_text = f"✅ {time_slot}"
                callback_data = f"time_{date}_{time_slot}"
            else:
                # Свободный слот
                button_text = time_slot
                callback_data = f"time_{date}_{time_slot}"
            
            available_slots.append(InlineKeyboardButton(button_text, callback_data=callback_data))
        
        keyboard = []
        for i in range(0, len(available_slots), 2):
            row = available_slots[i:i+2]
            keyboard.append(row)
        
        if selected_times:
            selected_text = ", ".join(selected_times)
            keyboard.append([InlineKeyboardButton(f"✅ Забронировать {selected_text}", callback_data=f"confirm_booking_{date}")])
        
        keyboard.append([InlineKeyboardButton("◀️ Back to calendar", callback_data="cal_back")])
        return InlineKeyboardMarkup(keyboard)

    def get_time_selection_message(self, date, selected_times=None):
        booked_slots = self.get_booked_slots(date)
        booked_text = f"\n🔴 **Занято:** {', '.join(booked_slots)}" if booked_slots else ""
        
        selected_text = ""
        if selected_times:
            selected_text = f"\n✅ **Выбрано:** {', '.join(selected_times)}"
        
        return f"""
🕐 **Выберите время для {date}:**{selected_text}{booked_text}

📍 **Инструкция:**
- ✅ Зеленые кнопки - свободные слоты
- 🔴 Красные кнопки - занятые слоты  
- Нажмите на зеленую кнопку чтобы выбрать
- Можно выбрать несколько слотов
- Каждый слот = 1 час

👇 **Выберите время нажатием на кнопку:**
"""