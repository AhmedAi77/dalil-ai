"""Translate domain errors to useful HTTP responses."""

from fastapi import HTTPException

from app.database.repositories import DocumentNotFoundError, DuplicateDocumentError
from app.services.document_processor import DocumentProcessingError
from app.services.embedding_service import EmbeddingError
from app.services.llm_service import LLMServiceError
from app.services.speech_service import SpeechServiceError
from app.services.vector_store import VectorStoreError


def to_http_exception(error: Exception) -> HTTPException:
    if isinstance(error, DocumentNotFoundError):
        return HTTPException(status_code=404, detail=str(error))
    if isinstance(error, DuplicateDocumentError):
        return HTTPException(status_code=409, detail=str(error))
    if isinstance(error, (DocumentProcessingError, ValueError)):
        return HTTPException(status_code=400, detail=str(error))
    if isinstance(error, (VectorStoreError, EmbeddingError, LLMServiceError)):
        return HTTPException(status_code=503, detail=str(error))
    if isinstance(error, SpeechServiceError):
        return HTTPException(status_code=422, detail=str(error))
    return HTTPException(status_code=500, detail="Unexpected application error")
