"""Extract and normalize supported document formats."""

import hashlib
import logging
from pathlib import Path
import re

from app.models.document import StructuredDocument
from app.services.extractors import (
    DocxExtractor,
    ExtractionError,
    PdfExtractor,
    TextExtractor,
    TxtExtractor,
    XlsxExtractor,
)

logger = logging.getLogger(__name__)


class DocumentProcessingError(ValueError):
    """Base error for failures that users can correct."""


class DocumentNotFoundError(DocumentProcessingError):
    """Raised when the supplied path does not exist."""


class DocumentPathError(DocumentProcessingError):
    """Raised when the supplied path is not a regular file."""


class UnsupportedDocumentTypeError(DocumentProcessingError):
    """Raised when no extractor exists for a document extension."""


class DocumentEncodingError(DocumentProcessingError):
    """Raised when a text document is not valid UTF-8."""


class EmptyDocumentError(DocumentProcessingError):
    """Raised when a document has no meaningful text after cleaning."""


class DocumentProcessor:
    """Turn a supported file into a validated, format-neutral document."""

    def __init__(self) -> None:
        self._extractors: dict[str, TextExtractor] = {
            ".txt": TxtExtractor(),
            ".md": TxtExtractor(),
            ".pdf": PdfExtractor(),
            ".docx": DocxExtractor(),
            ".xlsx": XlsxExtractor(),
            ".xlsm": XlsxExtractor(),
        }

    @property
    def supported_extensions(self) -> frozenset[str]:
        """Return the extensions accepted by this processor."""

        return frozenset(self._extractors)

    def process(self, source: str | Path) -> StructuredDocument:
        """Validate, extract, normalize, and describe one document."""

        path = Path(source).expanduser()
        logger.info("Document received: %s", path.name)

        if not path.exists():
            raise DocumentNotFoundError(f"Document does not exist: {path}")
        if not path.is_file():
            raise DocumentPathError(f"Document path is not a file: {path}")

        extension = path.suffix.lower()
        extractor = self._extractors.get(extension)
        if extractor is None:
            supported = ", ".join(sorted(self.supported_extensions))
            raise UnsupportedDocumentTypeError(
                f"Unsupported document type '{extension or '(none)'}'. "
                f"Supported types: {supported}"
            )

        try:
            raw_text = extractor.extract(path)
        except ExtractionError as exc:
            if "UTF-8" in str(exc):
                raise DocumentEncodingError(str(exc)) from exc
            raise DocumentProcessingError(str(exc)) from exc

        document = self.process_text(
            raw_text,
            filename=path.name,
            source=str(path.resolve()),
            extension=extension,
            size_bytes=path.stat().st_size,
        )
        logger.info(
            "Document processed: filename=%s characters=%d",
            document.filename,
            document.character_count,
        )
        return document

    def process_text(
        self,
        text: str,
        *,
        filename: str = "pasted-text.txt",
        source: str = "pasted://manual",
        extension: str = ".txt",
        size_bytes: int | None = None,
    ) -> StructuredDocument:
        """Normalize raw or pasted text into the same document contract."""

        content = self.clean_text(text)
        if not content:
            raise EmptyDocumentError(
                f"Document contains no meaningful text: {filename}"
            )
        return StructuredDocument(
            filename=filename,
            extension=extension.lower(),
            source=source,
            content=content,
            character_count=len(content),
            size_bytes=(
                size_bytes
                if size_bytes is not None
                else len(text.encode("utf-8"))
            ),
            content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
        )

    @staticmethod
    def clean_text(text: str) -> str:
        """Normalize line endings and whitespace while preserving paragraphs."""

        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        normalized = normalized.replace("\u00a0", " ").expandtabs(4)
        normalized = "\n".join(line.rstrip() for line in normalized.split("\n"))
        normalized = re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", normalized)
        return normalized.strip()
