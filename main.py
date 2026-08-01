import time
import logging
import re
from collections import defaultdict
from typing import Dict, List

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import (
    TELEGRAM_BOT_TOKEN,
    RATE_LIMIT_MESSAGES,
    RATE_LIMIT_WINDOW_SECONDS,
    MAX_HISTORY_MESSAGES,
    validate_config,
)
from database import init_db, save_message, get_recent_history, clear_history
from gemini_service import generate_ann_response

# Configure Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# In-memory rate limiting dictionary: {user_id: [timestamp1, timestamp2, ...]}
user_request_timestamps: Dict[int, List[float]] = defaultdict(list)


def is_rate_limited(user_id: int) -> bool:
    """
    Check if a user has exceeded the message rate limit.
    """
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS

    # Filter out timestamps older than the window
    user_request_timestamps[user_id] = [
        ts for ts in user_request_timestamps[user_id] if ts > cutoff
    ]

    if len(user_request_timestamps[user_id]) >= RATE_LIMIT_MESSAGES:
        return True

    user_request_timestamps[user_id].append(now)
    return False


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command with a warm, casual greeting from ANN."""
    if not update.message or not update.effective_user:
        return

    user_first_name = update.effective_user.first_name or "there"
    welcome_text = (
        f"Hey {user_first_name}! 👋 I'm ANN. Nice to connect with you!\n\n"
        "Epdi irukinga? How's your day going? Feel free to chat with me anytime in Tamil, Tanglish, or English! 😊"
    )
    await update.message.reply_text(welcome_text)


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /reset command to clear user chat history."""
    if not update.message or not update.effective_user:
        return

    user_id = update.effective_user.id
    await clear_history(user_id)
    await update.message.reply_text(
        "Seri, refreshed everything! We can start a fresh conversation now. What's up? 😊"
    )


async def split_and_send_message(update: Update, text: str, reply_to_message_id: int = None, max_length: int = 4000) -> None:
    """
    Split long messages into smaller chunks (<4000 chars) and send sequentially.
    """
    if not update.message:
        return

    if len(text) <= max_length:
        await update.message.reply_text(text, reply_to_message_id=reply_to_message_id)
        return

    # Split text into chunks respecting line breaks where possible
    chunks = []
    while len(text) > max_length:
        split_pos = text.rfind("\n", 0, max_length)
        if split_pos == -1:
            split_pos = max_length

        chunks.append(text[:split_pos])
        text = text[split_pos:].lstrip("\n")

    if text:
        chunks.append(text)

    is_first = True
    for chunk in chunks:
        if is_first:
            await update.message.reply_text(chunk, reply_to_message_id=reply_to_message_id)
            is_first = False
        else:
            await update.message.reply_text(chunk)


async def handle_chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return

    message = update.message
    text = message.text or ""

    # -------------------------
    # PRIVATE CHAT
    # -------------------------
    if update.effective_chat.type == "private":
        user_text = text.strip()

    # -------------------------
    # GROUPS / SUPERGROUPS
    # -------------------------
    else:
        bot = await context.bot.get_me()
        should_reply = False

        # If bot is mentioned
        if bot.username and f"@{bot.username.lower()}" in text.lower():
            should_reply = True

        # If someone says ANN or Ann
        elif "ann" in text.lower():
            should_reply = True

        # If replying to ANN's message
        elif (
            message.reply_to_message
            and message.reply_to_message.from_user
            and message.reply_to_message.from_user.id == bot.id
        ):
            should_reply = True

        # Ignore everything else
        if not should_reply:
            return

        # Remove @botname from message
        if bot.username:
            user_text = re.sub(rf"@{re.escape(bot.username)}", "", text, flags=re.IGNORECASE).strip()
        else:
            user_text = text.strip()

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # -------------------------
    # RATE LIMIT
    # -------------------------
    if is_rate_limited(user_id):
        reply_id = message.message_id if update.effective_chat.type != "private" else None
        await message.reply_text(
            "Dei slow down da haha! Typing super fast! 😅",
            reply_to_message_id=reply_id
        )
        return

    # -------------------------
    # TYPING
    # -------------------------
    try:
        await context.bot.send_chat_action(
            chat_id=chat_id,
            action=ChatAction.TYPING
        )
    except Exception:
        pass

    try:
        # Get history
        history = await get_recent_history(
            user_id,
            limit=MAX_HISTORY_MESSAGES
        )

        # Save user message
        await save_message(
            user_id=user_id,
            role="user",
            content=user_text
        )

        # Generate response
        ann_reply = await generate_ann_response(
            chat_history=history,
            latest_user_message=user_text,
            username=update.effective_user.username,
            first_name=update.effective_user.first_name
        )

        # Save ANN response
        await save_message(
            user_id=user_id,
            role="assistant",
            content=ann_reply
        )

        # Reply to user's message
        reply_id = message.message_id if update.effective_chat.type != "private" else None
        await split_and_send_message(update, ann_reply, reply_to_message_id=reply_id)

    except Exception as exc:
        logger.error(
            f"Error handling message: {exc}",
            exc_info=True
        )
        reply_id = message.message_id if update.effective_chat.type != "private" else None
        await message.reply_text(
            "Ayyoo! Konjam technical problem vandhuruku. Please message me once again. 😅",
            reply_to_message_id=reply_id
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler for the Telegram bot application."""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)


def main() -> None:
    """Initialize and run the Telegram bot."""
    validate_config()

    import asyncio
    try:
        asyncio.run(init_db())
    except RuntimeError:
        # If event loop is already running (e.g. in some environments)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(init_db())

    # Build python-telegram-bot Application
    application = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .concurrent_updates(True)
        .build()
    )

    # Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("reset", reset_command))

    # MessageHandler (capturing both private chats and group text messages)
    application.add_handler(
        MessageHandler(
            (filters.ChatType.PRIVATE | filters.ChatType.GROUPS) & filters.TEXT & (~filters.COMMAND),
            handle_chat_message,
        )
    )

    # Register error handler
    application.add_error_handler(error_handler)

    logger.info("ANN Bot is starting...")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
