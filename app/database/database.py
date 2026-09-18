"""Small SQLite connection and schema manager."""

from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Iterator


class Database:
    """Own SQLite connections and initialize the application schema."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    token_hash TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)"
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
                    filename TEXT NOT NULL,
                    extension TEXT NOT NULL,
                    source TEXT NOT NULL,
                    content TEXT NOT NULL,
                    content_hash TEXT NOT NULL UNIQUE,
                    character_count INTEGER NOT NULL CHECK(character_count > 0),
                    size_bytes INTEGER NOT NULL CHECK(size_bytes >= 0),
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_documents_created_at "
                "ON documents(created_at DESC)"
            )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(documents)").fetchall()
            }
            if "user_id" not in columns:
                connection.execute(
                    "ALTER TABLE documents ADD COLUMN user_id TEXT "
                    "REFERENCES users(id) ON DELETE CASCADE"
                )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_documents_user_created "
                "ON documents(user_id, created_at DESC)"
            )

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
