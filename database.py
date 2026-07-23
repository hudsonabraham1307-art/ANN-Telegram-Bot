"""
Database module for ANN Telegram Bot.
Handles async SQLite storage for per-user conversation memory using aiosqlite.
"""

import aiosqlite
import logging
from typing import List, Dict
from config import DATABASE_PATH, MAX_HISTORY_MESSAGES

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """Initialize SQLite database schema and indexes."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_user_id ON chat_history(user_id);
            """
        )
        await db.commit()
    logger.info(f"Database initialized successfully at '{DATABASE_PATH}'.")


async def save_message(user_id: int, role: str, content: str) -> None:
    """
    Save a message (user or model) to the database.

    :param user_id: Telegram user ID
    :param role: 'user' or 'model'
    :param content: Text content of the message
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """
            INSERT INTO chat_history (user_id, role, content)
            VALUES (?, ?, ?);
            """,
            (user_id, role, content),
        )
        await db.commit()


async def get_recent_history(user_id: int, limit: int = MAX_HISTORY_MESSAGES) -> List[Dict[str, str]]:
    """
    Fetch the last N messages for a specific user, ordered chronologically (oldest first).

    :param user_id: Telegram user ID
    :param limit: Maximum number of recent messages to fetch
    :return: List of dicts with 'role' and 'content' keys
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Get the latest 'limit' records for this user
        async with db.execute(
            """
            SELECT role, content FROM (
                SELECT role, content, id
                FROM chat_history
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
            ) ORDER BY id ASC;
            """,
            (user_id, limit),
        ) as cursor:
            rows = await cursor.fetchall()
            return [{"role": row[0], "content": row[1]} for row in rows]


async def clear_history(user_id: int) -> None:
    """
    Delete all chat history for a specific user.

    :param user_id: Telegram user ID
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM chat_history WHERE user_id = ?;", (user_id,))
        await db.commit()
    logger.info(f"Cleared chat history for user_id: {user_id}")
