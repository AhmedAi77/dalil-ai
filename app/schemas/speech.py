"""Speech-to-RAG schemas."""

from app.schemas.query import QueryResponse


class SpeechQueryResponse(QueryResponse):
    transcription: str
    language: str | None = None
