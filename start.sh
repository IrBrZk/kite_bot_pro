#!/bin/bash
set -e
cd /opt/kite_bot_pro || exit 1

# Use existing venv or create it
if [ -d "venv" ]; then
  source venv/bin/activate
else
  python3 -m venv venv
  source venv/bin/activate
  if [ -f requirements.txt ]; then
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
  fi
fi

# Main file — заменено на final_bot.py
MAIN_FILE="final_bot.py"
if [ ! -f "$MAIN_FILE" ]; then
  echo "ERROR: $MAIN_FILE not found in $(pwd)"
  exit 2
fi

# Запуск (systemd будет следить за процессом)
exec python3 "$MAIN_FILE"