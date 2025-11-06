#!/bin/bash
# Kite Bot Pro startup script with flock for local locking

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCKFILE="${SCRIPT_DIR}/kite_bot.lock"
VENV_DIR="${SCRIPT_DIR}/kite_bot_env"
PYTHON="${VENV_DIR}/bin/python3"

# Use flock to prevent multiple instances
exec 200>"${LOCKFILE}"
if ! flock -n 200; then
    echo "❌ Another instance of kite_bot is already running. Exiting."
    exit 1
fi

# Activate virtual environment
if [ -f "${VENV_DIR}/bin/activate" ]; then
    source "${VENV_DIR}/bin/activate"
else
    echo "❌ Virtual environment not found at ${VENV_DIR}"
    exit 1
fi

# Change to script directory
cd "${SCRIPT_DIR}"

# Run the bot
echo "🚀 Starting Kite Bot Pro..."
exec "${PYTHON}" final_bot.py
