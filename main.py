"""
Main module for Arthur Morgan Telegram Bot.

Features:
- Private chat replies
- Group chat replies
- Replies when bot is mentioned
- Replies when someone says "Ann" or "Arthur"
- Replies when someone replies to the bot's message
- Rate limiting
- Chat history
- Typing indicator
- Long message splitting
- OpenRouter AI responses
"""

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

from database import (
    init_db,
    save_message,
    get_recent_history,
    clear_history,
)

from gemini_service import generate_ann_response


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# ============================================================
# RATE LIMITING
# ============================================================

user_request_timestamps: Dict[int, List[float]] = defaultdict(list)


def is_rate_limited(user_id: int) -> bool:
    """
    Check whether a user has exceeded the configured rate limit.
    """

    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS

    # Remove timestamps outside the rate-limit window
    user_request_timestamps[user_id] = [
        timestamp
        for timestamp in user_request_timestamps[user_id]
        if timestamp > cutoff
    ]

    # User has reached the limit
    if len(user_request_timestamps[user_id]) >= RATE_LIMIT_MESSAGES:
        return True

    # Record this request
    user_request_timestamps[user_id].append(now)

    return False


# ============================================================
# /START
# ============================================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:

    if not update.message or not update.effective_user:
        return

    first_name = update.effective_user.first_name or "partner"

    welcome_text = (
        f"Well, hello there, {first_name}. 👋\n\n"
        "Name's Arthur. Arthur Morgan.\n"
        "You need something, or you just came here to bother me?"
    )

    await update.message.reply_text(welcome_text)


# ============================================================
# /RESET
# ============================================================

async def reset_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:

    if not update.message or not update.effective_user:
        return

    user_id = update.effective_user.id

    await clear_history(user_id)

    await update.message.reply_text(
        "Alright. Fresh start.\n"
        "Let's see where this goes."
    )


# ============================================================
# SEND LONG MESSAGE
# ============================================================

async def split_and_send_message(
    update: Update,
    text: str,
    reply_to_message_id: int = None,
    max_length: int = 4000
) -> None:

    if not update.message:
        return

    # Normal message
    if len(text) <= max_length:

        await update.message.reply_text(
            text,
            reply_to_message_id=reply_to_message_id
        )

        return

    # --------------------------------------------------------
    # Split long response
    # --------------------------------------------------------

    chunks = []

    while len(text) > max_length:

        split_pos = text.rfind(
            "\n",
            0,
            max_length
        )

        if split_pos == -1:
            split_pos = max_length

        chunks.append(
            text[:split_pos]
        )

        text = text[split_pos:].lstrip("\n")

    if text:
        chunks.append(text)

    # --------------------------------------------------------
    # Send chunks
    # --------------------------------------------------------

    first_chunk = True

    for chunk in chunks:

        if first_chunk:

            await update.message.reply_text(
                chunk,
                reply_to_message_id=reply_to_message_id
            )

            first_chunk = False

        else:

            await update.message.reply_text(
                chunk
            )


# ============================================================
# HANDLE CHAT MESSAGE
# ============================================================

async def handle_chat_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    if not update.effective_user:
        return

    if not update.effective_chat:
        return

    message = update.message

    text = message.text or ""

    chat_type = update.effective_chat.type


    # ========================================================
    # PRIVATE CHAT
    # ========================================================

    if chat_type == "private":

        user_text = text.strip()

        if not user_text:
            return


    # ========================================================
    # GROUP / SUPERGROUP
    # ========================================================

    else:

        # Get bot information
        bot = await context.bot.get_me()

        should_reply = False


        # ----------------------------------------------------
        # 1. BOT MENTION
        # ----------------------------------------------------

        if bot.username:

            mention_pattern = (
                rf"@{re.escape(bot.username)}"
            )

            if re.search(
                mention_pattern,
                text,
                flags=re.IGNORECASE
            ):

                should_reply = True


        # ----------------------------------------------------
        # 2. SOMEONE SAYS "ANN"
        # ----------------------------------------------------

        if not should_reply:

            if re.search(
                r"\bann\b",
                text,
                flags=re.IGNORECASE
            ):

                should_reply = True


        # ----------------------------------------------------
        # 3. SOMEONE SAYS "ARTHUR"
        # ----------------------------------------------------

        if not should_reply:

            if re.search(
                r"\barthur\b",
                text,
                flags=re.IGNORECASE
            ):

                should_reply = True


        # ----------------------------------------------------
        # 4. REPLY TO BOT'S MESSAGE
        # ----------------------------------------------------

        if not should_reply:

            if (
                message.reply_to_message
                and
                message.reply_to_message.from_user
                and
                message.reply_to_message.from_user.id == bot.id
            ):

                should_reply = True


        # ----------------------------------------------------
        # IGNORE NORMAL GROUP MESSAGES
        # ----------------------------------------------------

        if not should_reply:

            return


        # ----------------------------------------------------
        # REMOVE BOT MENTION
        # ----------------------------------------------------

        user_text = text

        if bot.username:

            user_text = re.sub(
                rf"@{re.escape(bot.username)}",
                "",
                user_text,
                flags=re.IGNORECASE
            )


        # ----------------------------------------------------
        # REMOVE "ANN" / "ARTHUR" ONLY WHEN APPROPRIATE
        # ----------------------------------------------------

        user_text = re.sub(
            r"\bann\b",
            "",
            user_text,
            flags=re.IGNORECASE
        )

        user_text = re.sub(
            r"\barthur\b",
            "",
            user_text,
            flags=re.IGNORECASE
        )

        user_text = user_text.strip()


        # ----------------------------------------------------
        # If message was only "Ann" / "Arthur"
        # ----------------------------------------------------

        if not user_text:

            user_text = (
                "Someone just called my name."
            )


    # ========================================================
    # USER INFORMATION
    # ========================================================

    user_id = update.effective_user.id

    chat_id = update.effective_chat.id


    # ========================================================
    # RATE LIMIT
    # ========================================================

    if is_rate_limited(user_id):

        reply_id = (
            message.message_id
            if chat_type != "private"
            else None
        )

        await message.reply_text(
            "Easy there. You're talking faster than I can keep up. 😅",
            reply_to_message_id=reply_id
        )

        return


    # ========================================================
    # TYPING INDICATOR
    # ========================================================

    try:

        await context.bot.send_chat_action(
            chat_id=chat_id,
            action=ChatAction.TYPING
        )

    except Exception as exc:

        logger.warning(
            f"Could not send typing action: {exc}"
        )


    # ========================================================
    # AI RESPONSE
    # ========================================================

    try:

        # ----------------------------------------------------
        # Get conversation history
        # ----------------------------------------------------

        history = await get_recent_history(
            user_id,
            limit=MAX_HISTORY_MESSAGES
        )


        # ----------------------------------------------------
        # Save user message
        # ----------------------------------------------------

        await save_message(
            user_id=user_id,
            role="user",
            content=user_text
        )


        # ----------------------------------------------------
        # Generate Arthur response
        # ----------------------------------------------------

        arthur_reply = await generate_ann_response(
            chat_history=history,
            latest_user_message=user_text,
            username=update.effective_user.username,
            first_name=update.effective_user.first_name
        )


        # ----------------------------------------------------
        # Save assistant response
        # ----------------------------------------------------

        await save_message(
            user_id=user_id,
            role="assistant",
            content=arthur_reply
        )


        # ----------------------------------------------------
        # Reply to message in groups
        # ----------------------------------------------------

        reply_id = (
            message.message_id
            if chat_type != "private"
            else None
        )


        await split_and_send_message(
            update,
            arthur_reply,
            reply_to_message_id=reply_id
        )


    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except Exception as exc:

        logger.error(
            f"Error handling message: {exc}",
            exc_info=True
        )

        reply_id = (
            message.message_id
            if chat_type != "private"
            else None
        )

        await message.reply_text(
            "Well... something went wrong on my end. "
            "Give it another shot.",
            reply_to_message_id=reply_id
        )


# ============================================================
# GLOBAL ERROR HANDLER
# ============================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
) -> None:

    logger.error(
        f"Exception while handling an update: {context.error}",
        exc_info=context.error
    )


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    # --------------------------------------------------------
    # Validate configuration
    # --------------------------------------------------------

    validate_config()


    # --------------------------------------------------------
    # Initialize database
    # --------------------------------------------------------

    import asyncio

    try:

        asyncio.run(
            init_db()
        )

    except RuntimeError:

        loop = asyncio.get_event_loop()

        loop.run_until_complete(
            init_db()
        )


    # --------------------------------------------------------
    # Build Telegram application
    # --------------------------------------------------------

    application = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .concurrent_updates(True)
        .build()
    )


    # --------------------------------------------------------
    # Commands
    # --------------------------------------------------------

    application.add_handler(
        CommandHandler(
            "start",
            start_command
        )
    )

    application.add_handler(
        CommandHandler(
            "reset",
            reset_command
        )
    )


    # --------------------------------------------------------
    # PRIVATE + GROUP + SUPERGROUP TEXT
    # --------------------------------------------------------

    application.add_handler(
        MessageHandler(
            (
                filters.ChatType.PRIVATE
                | filters.ChatType.GROUPS
            )
            & filters.TEXT
            & (~filters.COMMAND),
            handle_chat_message
        )
    )


    # --------------------------------------------------------
    # Error handler
    # --------------------------------------------------------

    application.add_error_handler(
        error_handler
    )


    # --------------------------------------------------------
    # Start bot
    # --------------------------------------------------------

    logger.info(
        "Arthur Morgan Telegram Bot is starting..."
    )

    application.run_polling(
        drop_pending_updates=True
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
