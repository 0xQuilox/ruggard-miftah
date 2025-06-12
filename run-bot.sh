#!/bin/bash

# Script to run the Twitter bot

# Exit on any error
set -e

# Define paths
SCRIPT_DIR=$(dirname "$(realpath "$0")")
PYTHON_SCRIPT="$SCRIPT_DIR/bot.py"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"
LOG_FILE="$SCRIPT_DIR/bot.log"
ENV_FILE="$SCRIPT_DIR/.env"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed. Please install Python 3.7 or higher."
    exit 1
fi

# Check if the Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: $PYTHON_SCRIPT not found in $SCRIPT_DIR"
    exit 1
fi

# Check if requirements.txt exists
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "Error: $REQUIREMENTS_FILE not found in $SCRIPT_DIR"
    exit 1
fi

# Create a virtual environment if it doesn't exist
VENV_DIR="$SCRIPT_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

# Activate the virtual environment
source "$VENV_DIR/bin/activate"

# Install dependencies from requirements.txt
echo "Installing dependencies from $REQUIREMENTS_FILE..."
pip install --upgrade pip
pip install -r "$REQUIREMENTS_FILE"

# Load environment variables from .env file if it exists
if [ -f "$ENV_FILE" ]; then
    echo "Loading environment variables from $ENV_FILE..."
    set -o allexport
    source "$ENV_FILE"
    set +o allexport
else
    echo "Warning: $ENV_FILE not found. Ensure environment variables are set."
fi

# Set environment variables for Twitter API keys (fallback to exported variables)
# Note: Replace placeholders with actual keys in .env or export manually
export CONSUMER_KEY="${CONSUMER_KEY:-your_consumer_key}"
export CONSUMER_SECRET="${CONSUMER_SECRET:-your_consumer_secret}"
export ACCESS_TOKEN="${ACCESS_TOKEN:-your_access_token}"
export ACCESS_TOKEN_SECRET="${ACCESS_TOKEN_SECRET:-your_access_token_secret}"
export BOT_HANDLE="${BOT_HANDLE:-YourBotHandle}"

# Check if all required environment variables are set
required_vars=("CONSUMER_KEY" "CONSUMER_SECRET" "ACCESS_TOKEN" "ACCESS_TOKEN_SECRET" "BOT_HANDLE")
missing_vars=()
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ] || [ "${!var}" = "your_${var,,}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo "Error: Missing or unset environment variables: ${missing_vars[*]}"
    echo "Please set them in $ENV_FILE or export them manually."
    exit 1
fi

# Run the bot and log output
echo "Starting Twitter bot at $(date)..."
echo "Logging to $LOG_FILE"
python3 "$PYTHON_SCRIPT" >> "$LOG_FILE" 2>&1 &

# Save the bot's PID
BOT_PID=$!
echo "Bot started with PID $BOT_PID"

# Wait briefly to ensure the bot starts without immediate errors
sleep 5
if ! ps -p $BOT_PID > /dev/null; then
    echo "Error: Bot failed to start. Check $LOG_FILE for details."
    cat "$LOG_FILE" | tail -n 20
    exit 1
fi

echo "Bot is running in the background. To stop it, run: kill $BOT_PID"
echo "To monitor logs, run: tail -f $LOG_FILE"

# Deactivate the virtual environment
deactivate