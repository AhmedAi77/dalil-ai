"""Repository methods keep SQL out of application services."""

from datetime import UTC, datetime
from hashlib import sha256
import sqlite3
from uuid import uuid4

from app.database.database import Database
from app.models.document import DocumentRecord, StructuredDocument


class DocumentNotFoundError(LookupError):
    """Raised when a requested document ID is absent."""


class DuplicateDocumentError(ValueError):
    """Raised when normalized content was already ingested."""


class DocumentRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(
        self,
        document: StructuredDocument,
        *,
        user_id: str | None = None,
        status: str = "processing",
    ) -> DocumentRecord:
        now = datetime.now(UTC)
        document_data = document.model_dump()
        if user_id:
            document_data["content_hash"] = sha256(
                f"{user_id}:{document.content_hash}".encode("utf-8")
            ).hexdigest()
        record = DocumentRecord(
            id=str(uuid4()),
            user_id=user_id,
            **document_data,
            status=status,
            created_at=now,
            updated_at=now,
        )
        try:
            with self.database.connect() as connection:
                connection.execute(
                    """
                    INSERT INTO documents (
                        id, user_id, filename, extension, source, content, content_hash,
                        character_count, size_bytes, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.id,
                        record.user_id,
                        record.filename,
                        record.extension,
                        record.source,
                        record.content,
                        record.content_hash,
                        record.character_count,
                        record.size_bytes,
                        record.status,
                        record.created_at.isoformat(),
                        record.updated_at.isoformat(),
                    ),
                )
        except sqlite3.IntegrityError as exc:
            if "content_hash" in str(exc):
                raise DuplicateDocumentError(
                    "A document with the same normalized content already exists"
                ) from exc
            raise
        return record

    def get(self, document_id: str, *, user_id: str | None = None) -> DocumentRecord | None:
        with self.database.connect() as connection:
            if user_id is None:
                row = connection.execute(
                    "SELECT * FROM documents WHERE id = ?", (document_id,)
                ).fetchone()
            else:
                row = connection.execute(
                    "SELECT * FROM documents WHERE id = ? AND user_id = ?",
                    (document_id, user_id),
                ).fetchone()
        return self._from_row(row) if row else None

    def require(self, document_id: str, *, user_id: str | None = None) -> DocumentRecord:
        record = self.get(document_id, user_id=user_id)
        if record is None:
            raise DocumentNotFoundError(f"Document not found: {document_id}")
        return record

    def list(self, *, user_id: str | None = None) -> list[DocumentRecord]:
        with self.database.connect() as connection:
            if user_id is None:
                rows = connection.execute(
                    "SELECT * FROM documents ORDER BY created_at DESC"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM documents WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,),
                ).fetchall()
        return [self._from_row(row) for row in rows]

    def update_status(self, document_id: str, status: str) -> DocumentRecord:
        now = datetime.now(UTC).isoformat()
        with self.database.connect() as connection:
            cursor = connection.execute(
                "UPDATE documents SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, document_id),
            )
        if cursor.rowcount == 0:
            raise DocumentNotFoundError(f"Document not found: {document_id}")
        return self.require(document_id)

    def delete(self, document_id: str, *, user_id: str | None = None) -> bool:
        with self.database.connect() as connection:
            if user_id is None:
                cursor = connection.execute(
                    "DELETE FROM documents WHERE id = ?", (document_id,)
                )
            else:
                cursor = connection.execute(
                    "DELETE FROM documents WHERE id = ? AND user_id = ?",
                    (document_id, user_id),
                )
        return cursor.rowcount > 0

    @staticmethod
    def _from_row(row: sqlite3.Row) -> DocumentRecord:
        return DocumentRecord(**dict(row))
