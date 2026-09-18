from pathlib import Path

import pytest

from app.database import AuthRepository, Database, DocumentRepository
from app.database.auth_repository import EmailAlreadyRegisteredError
from app.services.auth_service import AuthService, InvalidCredentialsError
from app.services.document_processor import DocumentProcessor


def build_auth(tmp_path: Path) -> tuple[AuthService, Database]:
    database = Database(tmp_path / "auth.db")
    database.initialize()
    return AuthService(AuthRepository(database), session_days=7), database


def test_registration_login_session_and_logout(tmp_path: Path) -> None:
    auth, _ = build_auth(tmp_path)

    user, registration_token = auth.register(
        name="Ahmed", email="AHMED@example.com", password="correct-horse"
    )

    assert user.email == "ahmed@example.com"
    assert user.password_hash != "correct-horse"
    assert auth.authenticate(registration_token) == user

    logged_in, login_token = auth.login(
        email="ahmed@example.com", password="correct-horse"
    )
    assert logged_in.id == user.id
    assert auth.authenticate(login_token) == user

    auth.logout(login_token)
    assert auth.authenticate(login_token) is None

    with pytest.raises(InvalidCredentialsError, match="Invalid email or password"):
        auth.login(email="ahmed@example.com", password="wrong-password")

    with pytest.raises(EmailAlreadyRegisteredError):
        auth.register(
            name="Duplicate", email="ahmed@example.com", password="another-password"
        )


def test_documents_are_isolated_by_user(tmp_path: Path) -> None:
    auth, database = build_auth(tmp_path)
    first, _ = auth.register(
        name="First User", email="first@example.com", password="password-one"
    )
    second, _ = auth.register(
        name="Second User", email="second@example.com", password="password-two"
    )
    documents = DocumentRepository(database)
    processed = DocumentProcessor().process_text(
        "The same content can belong to two private accounts.", filename="notes.md"
    )

    first_record = documents.create(processed, user_id=first.id)
    second_record = documents.create(processed, user_id=second.id)

    assert [item.id for item in documents.list(user_id=first.id)] == [first_record.id]
    assert [item.id for item in documents.list(user_id=second.id)] == [second_record.id]
    assert documents.get(first_record.id, user_id=second.id) is None
    assert documents.delete(first_record.id, user_id=second.id) is False
