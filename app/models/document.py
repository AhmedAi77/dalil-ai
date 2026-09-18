"""Models representing processed and persisted documents."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StructuredDocument(BaseModel):
    """A document after extraction, normalization, and validation."""

    model_config = ConfigDict(frozen=True)

    filename: str = Field(min_length=1)
    extension: str = Field(pattern=r"^\.[a-z0-9]+$")
    source: str = Field(min_length=1)
    content: str = Field(min_length=1)
    character_count: int = Field(gt=0)
    size_bytes: int = Field(ge=0)
    content_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


class DocumentRecord(StructuredDocument):
    """A document stored in SQLite."""

    id: str = Field(min_length=1)
    user_id: str | None = None
    status: str = Field(min_length=1)
    created_at: datetime
    updated_at: datetime
