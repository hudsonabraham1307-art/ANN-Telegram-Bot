import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)


# ============================================================
# API KEYS
# ============================================================

TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN",
    ""
).strip()

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    ""
).strip()


# ============================================================
# GEMINI MODEL
# ============================================================

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
).strip()


# ============================================================
# DATABASE
# ============================================================

DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    "ann_chat.db"
).strip()


# ============================================================
# MEMORY
# ============================================================

MAX_HISTORY_MESSAGES = int(
    os.getenv(
        "MAX_HISTORY_MESSAGES",
        "20"
    )
)


# ============================================================
# RATE LIMITS
# ============================================================

RATE_LIMIT_MESSAGES = int(
    os.getenv(
        "RATE_LIMIT_MESSAGES",
        "10"
    )
)

RATE_LIMIT_WINDOW_SECONDS = int(
    os.getenv(
        "RATE_LIMIT_WINDOW_SECONDS",
        "60"
    )
)


# ============================================================
# VALIDATE CONFIG
# ============================================================

def validate_config():

    missing = []

    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")

    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")

    if missing:

        print("\n" + "=" * 60)
        print("ERROR: Missing configuration values!\n")

        for item in missing:
            print(f"- {item}")

        print("\nAdd the missing variables and restart the bot.")
        print("=" * 60)

        sys.exit(1)


# ============================================================
# SAFE STARTUP INFO
# ============================================================

print("=" * 60)
print("GEMINI_MODEL =", GEMINI_MODEL)
print("=" * 60)
