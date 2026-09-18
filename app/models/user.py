"""Authentication domain models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    password_hash: str = Field(min_length=1)
    created_at: datetime
