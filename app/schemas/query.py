"""Question-answering schemas."""

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    document_id: str | None = None
    top_k: int | None = Field(default=None, ge=1, le=50)


class SourceReference(BaseModel):
    document_id: str
    filename: str
    chunk_index: int
    score: float


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceReference]
