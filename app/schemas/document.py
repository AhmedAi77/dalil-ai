"""Document API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class TextDocumentRequest(BaseModel):
    text: str = Field(min_length=1)
    title: str = Field(default="pasted-text", min_length=1, max_length=200)


class DocumentResponse(BaseModel):
    id: str
    filename: str
    extension: str
    source: str
    character_count: int
    size_bytes: int
    status: str
    created_at: datetime
    updated_at: datetime


class DeleteResponse(BaseModel):
    deleted: bool
    document_id: str
