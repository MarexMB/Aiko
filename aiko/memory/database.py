import json
import sqlite3
from pathlib import Path

from aiko.config import Settings


class Database:
    """Use only on the creating thread. Network workers receive plain copies."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA secure_delete = ON")
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY, character_id TEXT NOT NULL,
                title TEXT NOT NULL DEFAULT 'New chat',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY, session_id INTEGER NOT NULL
                    REFERENCES sessions(id) ON DELETE CASCADE,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS messages_session ON messages(session_id, id);
            CREATE TABLE IF NOT EXISTS preferences (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        """)

    def new_session(self, character_id: str) -> int:
        with self.connection:
            cursor = self.connection.execute(
                "INSERT INTO sessions(character_id) VALUES (?)", (character_id,)
            )
        return int(cursor.lastrowid)

    def sessions(self, character_id: str) -> list[dict]:
        return [dict(row) for row in self.connection.execute(
            "SELECT * FROM sessions WHERE character_id = ? ORDER BY id DESC", (character_id,)
        )]

    def add_message(self, session_id: int, role: str, content: str) -> None:
        if role not in {"user", "assistant"} or not content.strip() or len(content) > 32000:
            raise ValueError("Invalid message role, length or content.")
        with self.connection:
            self.connection.execute(
                "INSERT INTO messages(session_id, role, content) VALUES (?, ?, ?)",
                (session_id, role, content),
            )
            if role == "user":
                self.connection.execute(
                    "UPDATE sessions SET title = ? WHERE id = ? AND title = 'New chat'",
                    (" ".join(content.split())[:48], session_id),
                )

    def messages(self, session_id: int, limit: int = 100, before: int | None = None) -> list[dict]:
        rows = self.connection.execute(
            "SELECT * FROM messages WHERE session_id = ? AND id < ? ORDER BY id DESC LIMIT ?",
            (session_id, before if before is not None else 2**63 - 1, limit),
        ).fetchall()
        return [dict(row) for row in reversed(rows)]

    def delete_session(self, session_id: int) -> None:
        with self.connection:
            self.connection.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

    def delete_all(self) -> None:
        with self.connection:
            self.connection.execute("DELETE FROM sessions")

    def load_settings(self) -> Settings:
        row = self.connection.execute(
            "SELECT value FROM preferences WHERE key = ?", ("settings",)
        ).fetchone()
        return Settings.from_dict(json.loads(row[0])) if row else Settings()

    def save_settings(self, settings: Settings) -> None:
        with self.connection:
            self.connection.execute(
                "INSERT INTO preferences(key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                ("settings", json.dumps(settings.validate().to_dict())),
            )

    def close(self) -> None:
        self.connection.close()
