# Kite Bot — scaffold (refactor starter)

This scaffold provides a clean, modular starting point for refactoring the existing bot into a maintainable architecture.

Quick start:
1. Create a feature branch:
   git checkout -b feature/refactor-architecture

2. Copy files into repository as shown.

3. Create and activate a venv:
   python3 -m venv venv
   source venv/bin/activate

4. Install dependencies:
   pip install -r requirements.txt

5. Run the harness (doesn't require Telegram token):
   ./venv/bin/python tests/harness_callbacks.py

6. To run the bot (needs TELEGRAM_BOT_TOKEN env var):
   export TELEGRAM_BOT_TOKEN="your_token_here"
   ./venv/bin/python app/main.py

Notes:
- The scaffold is intentionally minimal. Move business logic from the legacy final_bot.py into services/* and handlers/*.
- Use tests/harness_callbacks.py to iteratively validate handlers without touching systemd or the production service.
