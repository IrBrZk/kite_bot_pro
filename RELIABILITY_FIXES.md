# Kite Bot Pro - Reliability Fixes

## Changes Summary

This document describes the fixes applied to improve the reliability and observability of the Telegram bot.

### 1. Error Handling (telegram.error.Conflict)

**Problem:** Multiple instances of the bot could start simultaneously, causing a `telegram.error.Conflict` error.

**Solution:** 
- Wrapped `application.run_polling()` in try/except to catch `telegram.error.Conflict`
- On Conflict: Log error at ERROR level with full details and exit with code 1
- Systemd `Restart=on-failure` will automatically restart with backoff
- Added flock-based locking in `start.sh` for local instance prevention

**Files modified:**
- `final_bot.py` (main function)
- `start.sh` (added flock locking)

### 2. Diagnostic Logging

**Problem:** Insufficient logging made it hard to diagnose issues in production.

**Solution:**
- Set DEBUG level for 'telegram' logger
- Set INFO level for 'httpx' logger  
- Added lightweight debug handlers at group=0:
  - `debug_message_handler`: Logs all messages with DEBUG_MSG prefix
  - `debug_callback_handler`: Logs all callback queries with DEBUG_CB prefix
- These handlers run first but don't interfere with conversation flow

**Files modified:**
- `final_bot.py` (logging configuration and debug handlers)

### 3. Language Selection Persistence

**Problem:** Language selection used print() statements and didn't persist to database.

**Solution:**
- Replaced all print() with logger.info/debug/error
- Added database update: `database_service.update_user(user_id, language=..., language_selected=True)`
- Added context.user_data['language'] fallback
- Added error handling for DB update failures
- Added DBG_LANG_HANDLER and DBG_GET_MAIN_MENU logging

**Files modified:**
- `final_bot.py` (handle_language_selection, get_main_menu)

### 4. Booking Flow Logging

**Problem:** No visibility into booking flow steps.

**Solution:**
- Added BOOKING_DATE logging when user selects date
- Added BOOKING_TIME logging when user selects time
- Added BOOKING_SAVE and BOOKING_CREATED logging when booking is saved

**Files modified:**
- `final_bot.py` (handle_calendar_callback, handle_time_selection, handle_final_confirmation)

### 5. Unknown Command Handler

**Problem:** Unknown commands had no graceful handling.

**Solution:**
- Added `unknown_command` handler that responds with "❌ Неизвестная команда"
- Returns user to main menu

**Files modified:**
- `final_bot.py` (unknown_command function)

### 6. ConversationHandler Settings

**Problem:** per_message=False could cause warnings with CallbackQuery handling.

**Solution:**
- Set `per_message=True` on ConversationHandler
- This allows proper handling of both messages and callback queries per user

**Files modified:**
- `final_bot.py` (ConversationHandler configuration)

### 7. Deployment Files

**Problem:** start.sh and systemd service had placeholder content.

**Solution:**

**start.sh:**
- Use flock for local locking to prevent multiple instances
- Activate virtual environment properly
- Use full path to python executable
- Exit with error if venv not found

**kite_bot_pro.service:**
- Set `Restart=on-failure` for automatic restart
- Set `RestartSec=10` for backoff
- Use `StandardOutput=journal` and `StandardError=journal` for logging
- Set proper WorkingDirectory and ExecStart paths

**Files modified:**
- `start.sh`
- `kite_bot_pro.service`

## Testing Instructions

### Local Testing

1. **Install dependencies:**
   ```bash
   python3 -m venv kite_bot_env
   source kite_bot_env/bin/activate
   pip install -r requirements.txt
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your TELEGRAM_BOT_TOKEN
   ```

3. **Test bot startup:**
   ```bash
   ./start.sh
   ```
   
   Expected: Bot starts and logs "🚀 Финальный бот запущен с новой логикой бронирования!"

4. **Test Conflict handling:**
   ```bash
   # In terminal 1:
   ./start.sh
   
   # In terminal 2:
   ./start.sh
   ```
   
   Expected: Second instance exits with "❌ Another instance of kite_bot is already running"

5. **Test language selection:**
   - Send `/start` to bot
   - Select a language (e.g., "🇷🇺 Russian")
   - Check logs for `DBG_LANG_HANDLER` entries
   - Restart bot and verify language persists

6. **Test booking flow:**
   - Start booking process
   - Select a date - check logs for `BOOKING_DATE` entry
   - Select a time - check logs for `BOOKING_TIME` entry
   - Complete booking - check logs for `BOOKING_SAVE` and `BOOKING_CREATED` entries

7. **Test debug logging:**
   - Send any message to bot
   - Check logs for `DEBUG_MSG` entry with user_id, chat_id, and text
   - Click any inline button
   - Check logs for `DEBUG_CB` entry with callback data

### Systemd Testing

1. **Install service:**
   ```bash
   sudo cp kite_bot_pro.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable kite_bot_pro
   ```

2. **Start service:**
   ```bash
   sudo systemctl start kite_bot_pro
   sudo systemctl status kite_bot_pro
   ```

3. **Test auto-restart on failure:**
   ```bash
   # Manually stop the bot process (not the service)
   sudo pkill -f final_bot.py
   
   # Wait 10 seconds, then check status
   sleep 10
   sudo systemctl status kite_bot_pro
   ```
   
   Expected: Service should auto-restart

4. **View logs:**
   ```bash
   sudo journalctl -u kite_bot_pro -f
   ```

## Security

CodeQL scan completed with 0 vulnerabilities found.

## Rollback

If issues occur:

1. **Stop the service:**
   ```bash
   sudo systemctl stop kite_bot_pro
   ```

2. **Revert to previous version:**
   ```bash
   git checkout feat/start-final-bot
   ```

3. **Restart:**
   ```bash
   sudo systemctl start kite_bot_pro
   ```

## Monitoring

Key log patterns to monitor:

- `❌ telegram.error.Conflict` - Multiple instances detected
- `DBG_LANG_HANDLER` - Language selection events
- `BOOKING_DATE`, `BOOKING_TIME`, `BOOKING_SAVE` - Booking flow events
- `DEBUG_MSG`, `DEBUG_CB` - All user interactions
- `❌ Unhandled exception` - Unexpected errors

## Known Limitations

- Debug handlers log at DEBUG level for all messages/callbacks. In high-volume scenarios, consider adding a config flag to disable.
- Database update failures in language selection are logged but don't block the operation (language is saved in memory).
