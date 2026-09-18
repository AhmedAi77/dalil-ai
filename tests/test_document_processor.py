"""Tests for the first ingestion component."""

from pathlib import Path

import pytest

from app.services.document_processor import (
    DocumentEncodingError,
    DocumentNotFoundError,
    DocumentPathError,
    DocumentProcessor,
    EmptyDocumentError,
    UnsupportedDocumentTypeError,
)


@pytest.fixture
def processor() -> DocumentProcessor:
    return DocumentProcessor()


def test_process_valid_txt_file(
    processor: DocumentProcessor, tmp_path: Path
) -> None:
    source = tmp_path / "docker_notes.TXT"
    source.write_text("Docker is a container platform.\n", encoding="utf-8")

    document = processor.process(source)

    assert document.filename == "docker_notes.TXT"
    assert document.extension == ".txt"
    assert document.content == "Docker is a container platform."
    assert document.character_count == len(document.content)
    assert document.size_bytes == source.stat().st_size
    assert document.source == str(source.resolve())


def test_process_markdown_as_utf8_text(
    processor: DocumentProcessor, tmp_path: Path
) -> None:
    source = tmp_path / "knowledge.md"
    source.write_text("# Architecture\n\nSQLite stores documents.", encoding="utf-8")

    document = processor.process(source)

    assert document.extension == ".md"
    assert document.content.startswith("# Architecture")


def test_clean_text_normalizes_whitespace(processor: DocumentProcessor) -> None:
    raw = "  Heading  \r\n\r\n\r\nLine with tab\t  \rFinal\u00a0line  "

    cleaned = processor.clean_text(raw)

    assert cleaned == "Heading\n\nLine with tab\nFinal line"


def test_missing_file_is_rejected(
    processor: DocumentProcessor, tmp_path: Path
) -> None:
    with pytest.raises(DocumentNotFoundError, match="does not exist"):
        processor.process(tmp_path / "missing.txt")


def test_directory_is_rejected(
    processor: DocumentProcessor, tmp_path: Path
) -> None:
    with pytest.raises(DocumentPathError, match="not a file"):
        processor.process(tmp_path)


def test_unsupported_extension_is_rejected(
    processor: DocumentProcessor, tmp_path: Path
) -> None:
    source = tmp_path / "notes.csv"
    source.write_text("not,supported", encoding="utf-8")

    with pytest.raises(UnsupportedDocumentTypeError, match="Unsupported"):
        processor.process(source)


@pytest.mark.parametrize("text", ["", "   \n\t\n  "])
def test_empty_document_is_rejected(
    processor: DocumentProcessor, tmp_path: Path, text: str
) -> None:
    source = tmp_path / "empty.txt"
    source.write_text(text, encoding="utf-8")

    with pytest.raises(EmptyDocumentError, match="no meaningful text"):
        processor.process(source)


def test_non_utf8_document_is_rejected(
    processor: DocumentProcessor, tmp_path: Path
) -> None:
    source = tmp_path / "latin1.txt"
    source.write_bytes("café".encode("latin-1"))

    with pytest.raises(DocumentEncodingError, match="UTF-8"):
        processor.process(source)
