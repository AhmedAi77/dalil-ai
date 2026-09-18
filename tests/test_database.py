from pathlib import Path

import pytest

from app.database import Database, DocumentRepository, DuplicateDocumentError
from app.services.document_processor import DocumentProcessor


@pytest.fixture
def repository(tmp_path: Path) -> DocumentRepository:
    database = Database(tmp_path / "test.db")
    database.initialize()
    return DocumentRepository(database)


def test_document_crud(repository: DocumentRepository) -> None:
    document = DocumentProcessor().process_text("Useful local knowledge.")

    created = repository.create(document)
    assert repository.get(created.id) == created
    assert repository.list() == [created]

    indexed = repository.update_status(created.id, "indexed")
    assert indexed.status == "indexed"
    assert indexed.updated_at >= created.updated_at

    assert repository.delete(created.id) is True
    assert repository.get(created.id) is None


def test_duplicate_normalized_content_is_rejected(
    repository: DocumentRepository,
) -> None:
    processor = DocumentProcessor()
    repository.create(processor.process_text("Same content", filename="one.txt"))

    with pytest.raises(DuplicateDocumentError):
        repository.create(
            processor.process_text("  Same content  ", filename="renamed.txt")
        )
