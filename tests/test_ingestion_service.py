from pathlib import Path

import pytest

from app.database import Database, DocumentRepository
from app.services.chunker import Chunker
from app.services.document_processor import DocumentProcessor
from app.services.ingestion_service import IngestionService


class FakeEmbeddings:
    dimension = 3

    def embed_documents(self, chunks):
        return [[1.0, 0.0, 0.0] for _ in chunks]


class FakeVectorStore:
    def __init__(self) -> None:
        self.dimension = None
        self.chunks = []
        self.deleted = []

    def ensure_index(self, dimension):
        self.dimension = dimension

    def upsert(self, chunks, vectors, *, user_id=None):
        self.chunks = list(chunks)

    def delete_document(self, document_id, *, user_id=None):
        self.deleted.append(document_id)


def test_ingestion_and_deletion_coordinate_both_stores(tmp_path: Path) -> None:
    database = Database(tmp_path / "documents.db")
    database.initialize()
    repository = DocumentRepository(database)
    vectors = FakeVectorStore()
    service = IngestionService(
        DocumentProcessor(),
        repository,
        Chunker(chunk_size=20, overlap=5),
        FakeEmbeddings(),
        vectors,
    )

    record = service.ingest_text(
        "Docker logs explain why the daemon failed.", title="docker"
    )

    assert record.status == "indexed"
    assert vectors.dimension == 3
    assert len(vectors.chunks) > 1
    assert all(chunk.document_id == record.id for chunk in vectors.chunks)

    assert service.delete(record.id) is True
    assert vectors.deleted == [record.id]
    assert repository.get(record.id) is None


def test_file_ingestion_uses_required_display_title(tmp_path: Path) -> None:
    database = Database(tmp_path / "documents.db")
    database.initialize()
    repository = DocumentRepository(database)
    service = IngestionService(
        DocumentProcessor(),
        repository,
        Chunker(chunk_size=100, overlap=10),
        FakeEmbeddings(),
        FakeVectorStore(),
    )
    source = tmp_path / "original-name.md"
    source.write_text("# Product notes\n\nMarkdown stays searchable.", encoding="utf-8")

    record = service.ingest_path(str(source), title="Launch Brief")

    assert record.filename == "Launch Brief.md"
    assert record.extension == ".md"

    with pytest.raises(ValueError, match="title is required"):
        service.ingest_text("Some useful content", title="   ")
