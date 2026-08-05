import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# API Keys
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
).strip()

print("=" * 60)
print("OPENROUTER_MODEL =", OPENROUTER_MODEL)
print("=" * 60)

# Database
DATABASE_PATH = os.getenv("DATABASE_PATH", "ann_chat.db").strip()

# Memory
MAX_HISTORY_MESSAGES = int(
    os.getenv("MAX_HISTORY_MESSAGES", "20")
)

# Rate Limits
RATE_LIMIT_MESSAGES = int(
    os.getenv("RATE_LIMIT_MESSAGES", "10")
)

RATE_LIMIT_WINDOW_SECONDS = int(
    os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")
)


def validate_config():
    missing = []

    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")

    if not OPENROUTER_API_KEY:
        missing.append("OPENROUTER_API_KEY")

    if missing:
        print("\n" + "=" * 60)
        print("ERROR: Missing configuration values!\n")

        for item in missing:
            print(f"- {item}")

        print("\nUpdate your .env file and try again.")
        print("=" * 60)
        sys.exit(1)
