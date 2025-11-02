from enum import IntEnum, Enum

class States(IntEnum):
    MAIN_MENU = 0
    LANGUAGE_SELECTION = 1
    BOOKING_DATE = 2
    BOOKING_TIME = 3
    BOOKING_LOCATION_CHOICE = 4
    BOOKING_LOT_SELECTION = 5
    BOOKING_CONTACTS = 6
    BOOKING_FINAL_CONFIRM = 7
    LEVEL_TEST_Q1 = 10
    LEVEL_TEST_Q2 = 11
    LEVEL_TEST_Q3 = 12
    LEVEL_TEST_Q4 = 13
    LEVEL_TEST_Q5 = 14

class BookingStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

# Устаревшее (если где-то используется) — оставим для совместимости
BOOKING_STATUS = BookingStatus

SUPPORTED_LANGUAGES = {
    'en': 'English',
    'ru': 'Русский',
    'ar': 'العربية'
}
