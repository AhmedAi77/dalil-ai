"""Models used by chunking and retrieval."""

from pydantic import BaseModel, ConfigDict, Field


class DocumentChunk(BaseModel):
    """A traceable piece of a persisted document."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    chunk_index: int = Field(ge=0)
    text: str = Field(min_length=1)
    character_count: int = Field(gt=0)


class RetrievedChunk(DocumentChunk):
    """A chunk returned by semantic search."""

    score: float
