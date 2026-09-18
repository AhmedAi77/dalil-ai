"""Coordinate processing, persistence, chunking, embedding, and indexing."""

import logging
from pathlib import Path

from app.database.repositories import DocumentRepository
from app.models.document import DocumentRecord, StructuredDocument
from app.services.chunker import Chunker
from app.services.document_processor import DocumentProcessor
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import PineconeVectorStore

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(
        self,
        processor: DocumentProcessor,
        repository: DocumentRepository,
        chunker: Chunker,
        embeddings: EmbeddingService,
        vector_store: PineconeVectorStore,
        owned_upload_dir: Path | None = None,
    ) -> None:
        self.processor = processor
        self.repository = repository
        self.chunker = chunker
        self.embeddings = embeddings
        self.vector_store = vector_store
        self.owned_upload_dir = owned_upload_dir.resolve() if owned_upload_dir else None

    def ingest_path(
        self, path: str, *, title: str | None = None, user_id: str | None = None
    ) -> DocumentRecord:
        document = self.processor.process(path)
        if title is not None:
            safe_title = self._safe_title(title)
            document = document.model_copy(
                update={"filename": f"{safe_title}{document.extension}"}
            )
        return self._ingest(document, user_id=user_id)

    def ingest_text(
        self, text: str, *, title: str = "pasted-text", user_id: str | None = None
    ) -> DocumentRecord:
        safe_title = self._safe_title(title)
        document = self.processor.process_text(
            text,
            filename=f"{safe_title}.txt",
            source=f"pasted://{safe_title}",
        )
        return self._ingest(document, user_id=user_id)

    @staticmethod
    def _safe_title(title: str) -> str:
        safe_title = "".join(
            char for char in title.strip() if char.isalnum() or char in "-_ "
        ).strip()
        if not safe_title:
            raise ValueError("Document title is required")
        return safe_title

    def _ingest(
        self, document: StructuredDocument, *, user_id: str | None = None
    ) -> DocumentRecord:
        record = self.repository.create(document, user_id=user_id)
        try:
            chunks = self.chunker.split(
                record.content,
                document_id=record.id,
                filename=record.filename,
            )
            vectors = self.embeddings.embed_documents(chunks)
            self.vector_store.ensure_index(self.embeddings.dimension)
            self.vector_store.upsert(chunks, vectors, user_id=user_id)
            indexed = self.repository.update_status(record.id, "indexed")
            logger.info(
                "Document indexed: id=%s chunks=%d", indexed.id, len(chunks)
            )
            return indexed
        except Exception:
            try:
                self.vector_store.delete_document(record.id, user_id=user_id)
            except Exception:
                logger.exception("Failed to clean vectors after ingestion error")
            self.repository.delete(record.id)
            raise

    def delete(self, document_id: str, *, user_id: str | None = None) -> bool:
        record = self.repository.require(document_id, user_id=user_id)
        self.vector_store.delete_document(document_id, user_id=user_id)
        deleted = self.repository.delete(document_id, user_id=user_id)
        self._delete_owned_upload(record.source)
        logger.info("Document deleted: id=%s", document_id)
        return deleted

    def _delete_owned_upload(self, source: str) -> None:
        if self.owned_upload_dir is None or source.startswith("pasted://"):
            return
        path = Path(source)
        try:
            resolved = path.resolve()
            if resolved.is_relative_to(self.owned_upload_dir):
                resolved.unlink(missing_ok=True)
        except OSError:
            logger.exception("Could not remove managed upload: %s", path.name)
