"""SQLite persistence package."""

from app.database.database import Database
from app.database.auth_repository import AuthRepository
from app.database.repositories import DocumentRepository, DuplicateDocumentError

__all__ = ["AuthRepository", "Database", "DocumentRepository", "DuplicateDocumentError"]
