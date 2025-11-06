# services/admin.py
import logging
import sqlite3
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AdminManager:
    def __init__(self, database):
        self.db = database
        self.admin_ids = [224853932]
    
    def is_admin(self, user_id):
        return user_id in self.admin_ids
    
    def get_today_stats(self):
        today = datetime.now().strftime('%Y-%m-%d')
        try:
            with sqlite3.connect('kite_bot.db') as conn:
                today_bookings = conn.execute(
                    'SELECT COUNT(*) FROM schedule_slots WHERE date = ?', 
                    (today,)
                ).fetchone()[0]
                
                total_users = self.db.get_total_users_count()
                total_bookings = self.db.get_total_bookings_count()
                
                status_stats = conn.execute(
                    'SELECT status, COUNT(*) FROM schedule_slots GROUP BY status'
                ).fetchall()
                
            return {
                'today_bookings': today_bookings,
                'total_users': total_users,
                'total_bookings': total_bookings,
                'status_stats': dict(status_stats)
            }
        except Exception as e:
            logger.error(f"Error getting today stats: {e}")
            return {'today_bookings': 0, 'total_users': 0, 'total_bookings': 0, 'status_stats': {}}
    
    def get_recent_bookings(self, limit=10):
        try:
            with sqlite3.connect('kite_bot.db') as conn:
                cursor = conn.execute('''
                    SELECT s.id, s.date, s.time, s.student_name, s.status, u.telegram_username 
                    FROM schedule_slots s 
                    LEFT JOIN users u ON s.user_id = u.user_id 
                    ORDER BY s.created_at DESC 
                    LIMIT ?
                ''', (limit,))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting recent bookings: {e}")
            return []
    
    def get_user_stats(self):
        try:
            with sqlite3.connect('kite_bot.db') as conn:
                cursor = conn.execute('SELECT language, COUNT(*) FROM users GROUP BY language')
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return []
    
    def get_booking_stats_by_date(self, days=7):
        dates = []
        stats = []
        try:
            for i in range(days):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                with sqlite3.connect('kite_bot.db') as conn:
                    count = conn.execute(
                        'SELECT COUNT(*) FROM schedule_slots WHERE date = ?', 
                        (date,)
                    ).fetchone()[0]
                dates.append(date)
                stats.append(count)
            return list(zip(dates, stats))
        except Exception as e:
            logger.error(f"Error getting booking stats: {e}")
            return []
    
    def get_all_bookings(self, date=None):
        try:
            with sqlite3.connect('kite_bot.db') as conn:
                if date:
                    cursor = conn.execute('''
                        SELECT s.id, s.date, s.time, s.student_name, s.status, u.telegram_username, u.phone
                        FROM schedule_slots s 
                        LEFT JOIN users u ON s.user_id = u.user_id 
                        WHERE s.date = ?
                        ORDER BY s.time
                    ''', (date,))
                else:
                    cursor = conn.execute('''
                        SELECT s.id, s.date, s.time, s.student_name, s.status, u.telegram_username, u.phone
                        FROM schedule_slots s 
                        LEFT JOIN users u ON s.user_id = u.user_id 
                        ORDER BY s.date DESC, s.time DESC
                    ''')
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting all bookings: {e}")
            return []