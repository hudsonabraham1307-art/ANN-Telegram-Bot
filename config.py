import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "google/gemma-3-27b-it:free"
)

DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    "ann_chat.db"
)

MAX_HISTORY_MESSAGES = int(
    os.getenv("MAX_HISTORY_MESSAGES", 20)
)

RATE_LIMIT_MESSAGES = int(
    os.getenv("RATE_LIMIT_MESSAGES", 10)
)

RATE_LIMIT_WINDOW_SECONDS = int(
    os.getenv("RATE_LIMIT_WINDOW_SECONDS", 60)
)


def validate_config():
    required = [
        TELEGRAM_BOT_TOKEN,
        OPENROUTER_API_KEY
    ]

    if not all(required):
        raise ValueError("Missing required environment variables")
