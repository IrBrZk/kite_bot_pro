# database.py
import sqlite3
import logging
import os

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path='kite_bot.db'):
        self.db_path = db_path
        logger.info(f"📁 Database path: {os.path.abspath(self.db_path)}")
        self.init_database()
    
    def init_database(self):
        """Инициализировать базу данных с правильной структурой"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Таблица пользователей
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        name TEXT,
                        telegram_username TEXT,
                        phone TEXT,
                        language TEXT DEFAULT 'en',
                        level TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Таблица бронирований
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS schedule_slots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT,
                        time TEXT,
                        user_id INTEGER,
                        student_name TEXT,
                        lesson_type TEXT DEFAULT 'beginner',
                        status TEXT DEFAULT 'booked',
                        location TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')
                conn.commit()
                logger.info("✅ Database initialized successfully")
                
        except Exception as e:
            logger.error(f"❌ Error initializing database: {e}")
            raise
    
    def save_user(self, user_id, name=None, telegram_username=None, phone=None, level=None):
        """Сохранить/обновить пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO users (user_id, name, telegram_username, phone, level)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, name, telegram_username, phone, level))
                conn.commit()
                logger.info(f"User {user_id} saved/updated")
        except Exception as e:
            logger.error(f"Error saving user {user_id}: {e}")
    
    def get_user(self, user_id):
        """Получить пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    def get_user_bookings(self, user_id):
        """Получить бронирования пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    'SELECT date, time, student_name, lesson_type, status FROM schedule_slots WHERE user_id = ? ORDER BY date, time',
                    (user_id,)
                )
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting user bookings {user_id}: {e}")
            return []
    
    def get_all_users(self):
        """Получить всех пользователей"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('SELECT * FROM users ORDER BY created_at DESC')
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    def get_total_users_count(self):
        """Получить общее количество пользователей"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('SELECT COUNT(*) FROM users')
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting total users count: {e}")
            return 0
    
    def get_total_bookings_count(self):
        """Получить общее количество бронирований"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('SELECT COUNT(*) FROM schedule_slots')
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting total bookings count: {e}")
            return 0
    
    def save_booking(self, date, time, user_id, student_name, lesson_type='beginner', status='booked', location=None):
        """Сохранить бронирование"""
        try:
            logger.info(f"💾 Saving booking: {date} {time} for {student_name}")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    INSERT INTO schedule_slots (date, time, user_id, student_name, lesson_type, status, location)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (date, time, user_id, student_name, lesson_type, status, location))
                conn.commit()
                
                booking_id = cursor.lastrowid
                logger.info(f"✅ Booking saved! ID: {booking_id}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error saving booking: {e}")
            return False
    
    def get_booked_slots(self, date):
        """Получить занятые слоты на дату"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    'SELECT time FROM schedule_slots WHERE date = ? AND status IN ("booked", "confirmed") ORDER BY time',
                    (date,)
                )
                slots = [row[0] for row in cursor.fetchall()]
                logger.info(f"📊 Booked slots for {date}: {len(slots)} slots")
                return slots
        except Exception as e:
            logger.error(f"❌ Error getting booked slots: {e}")
            return []
    
    def get_all_bookings(self):
        """Получить все бронирования"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('SELECT * FROM schedule_slots ORDER BY created_at DESC')
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting all bookings: {e}")
            return []