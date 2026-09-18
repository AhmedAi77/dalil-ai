"""SQLite persistence for users and opaque server-side sessions."""

from datetime import UTC, datetime
import sqlite3
from uuid import uuid4

from app.database.database import Database
from app.models.user import UserRecord


class EmailAlreadyRegisteredError(ValueError):
    pass


class AuthRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create_user(self, *, email: str, name: str, password_hash: str) -> UserRecord:
        user = UserRecord(
            id=str(uuid4()),
            email=email.strip().lower(),
            name=name.strip(),
            password_hash=password_hash,
            created_at=datetime.now(UTC),
        )
        try:
            with self.database.connect() as connection:
                connection.execute(
                    "INSERT INTO users (id, email, name, password_hash, created_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (user.id, user.email, user.name, user.password_hash, user.created_at.isoformat()),
                )
        except sqlite3.IntegrityError as exc:
            raise EmailAlreadyRegisteredError(
                "An account with this email already exists"
            ) from exc
        return user

    def get_user_by_email(self, email: str) -> UserRecord | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email.strip(),)
            ).fetchone()
        return UserRecord(**dict(row)) if row else None

    def create_session(self, *, token_hash: str, user_id: str, expires_at: datetime) -> None:
        now = datetime.now(UTC).isoformat()
        with self.database.connect() as connection:
            connection.execute("DELETE FROM sessions WHERE expires_at <= ?", (now,))
            connection.execute(
                "INSERT INTO sessions (token_hash, user_id, expires_at, created_at) "
                "VALUES (?, ?, ?, ?)",
                (token_hash, user_id, expires_at.isoformat(), now),
            )

    def user_for_session(self, token_hash: str) -> UserRecord | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT users.* FROM sessions
                JOIN users ON users.id = sessions.user_id
                WHERE sessions.token_hash = ? AND sessions.expires_at > ?
                """,
                (token_hash, datetime.now(UTC).isoformat()),
            ).fetchone()
        return UserRecord(**dict(row)) if row else None

    def delete_session(self, token_hash: str) -> None:
        with self.database.connect() as connection:
            connection.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
