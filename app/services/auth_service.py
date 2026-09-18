"""Password authentication and opaque server-side session management."""

from datetime import UTC, datetime, timedelta
from functools import lru_cache
from hashlib import sha256
import secrets

from pwdlib import PasswordHash

from app.config import get_settings
from app.database import AuthRepository, Database
from app.models.user import UserRecord


class InvalidCredentialsError(ValueError):
    pass


class AuthService:
    def __init__(self, repository: AuthRepository, *, session_days: int = 7) -> None:
        self.repository = repository
        self.session_days = session_days
        self.passwords = PasswordHash.recommended()
        self._dummy_hash = self.passwords.hash("contexta-dummy-password")

    def register(self, *, name: str, email: str, password: str) -> tuple[UserRecord, str]:
        user = self.repository.create_user(
            email=email,
            name=name,
            password_hash=self.passwords.hash(password),
        )
        return user, self._new_session(user.id)

    def login(self, *, email: str, password: str) -> tuple[UserRecord, str]:
        user = self.repository.get_user_by_email(email)
        password_hash = user.password_hash if user else self._dummy_hash
        valid = self.passwords.verify(password, password_hash)
        if user is None or not valid:
            raise InvalidCredentialsError("Invalid email or password")
        return user, self._new_session(user.id)

    def authenticate(self, token: str | None) -> UserRecord | None:
        if not token:
            return None
        return self.repository.user_for_session(self._token_hash(token))

    def logout(self, token: str | None) -> None:
        if token:
            self.repository.delete_session(self._token_hash(token))

    def _new_session(self, user_id: str) -> str:
        token = secrets.token_urlsafe(32)
        self.repository.create_session(
            token_hash=self._token_hash(token),
            user_id=user_id,
            expires_at=datetime.now(UTC) + timedelta(days=self.session_days),
        )
        return token

    @staticmethod
    def _token_hash(token: str) -> str:
        return sha256(token.encode("utf-8")).hexdigest()


@lru_cache(maxsize=1)
def get_auth_service() -> AuthService:
    settings = get_settings()
    database = Database(settings.database_path)
    database.initialize()
    return AuthService(
        AuthRepository(database), session_days=settings.auth_session_days
    )
