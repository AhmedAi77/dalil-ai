"""Lazy, reusable local sentence-transformer embeddings."""

from collections.abc import Sequence
from typing import Any

from app.models.chunk import DocumentChunk


class EmbeddingError(RuntimeError):
    """Raised when the local embedding model cannot encode text."""


class EmbeddingService:
    def __init__(self, model_name: str, model: Any | None = None) -> None:
        self.model_name = model_name
        self._model = model

    @property
    def model(self) -> Any:
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.model_name)
            except Exception as exc:
                raise EmbeddingError(
                    f"Could not load embedding model '{self.model_name}'"
                ) from exc
        return self._model

    @property
    def dimension(self) -> int:
        dimension_getter = getattr(self.model, "get_embedding_dimension", None)
        if dimension_getter is None:
            dimension_getter = self.model.get_sentence_embedding_dimension
        configured = dimension_getter()
        if configured is not None:
            return int(configured)
        return len(self.embed_text("dimension probe"))

    def embed_text(self, text: str) -> list[float]:
        if not text.strip():
            raise ValueError("Text to embed cannot be empty")
        try:
            vector = self.model.encode(text, normalize_embeddings=True)
            return self._as_list(vector)
        except Exception as exc:
            raise EmbeddingError("Could not generate text embedding") from exc

    def embed_documents(
        self, chunks: Sequence[DocumentChunk]
    ) -> list[list[float]]:
        if not chunks:
            return []
        try:
            vectors = self.model.encode(
                [chunk.text for chunk in chunks], normalize_embeddings=True
            )
            return [self._as_list(vector) for vector in vectors]
        except Exception as exc:
            raise EmbeddingError("Could not generate document embeddings") from exc

    @staticmethod
    def _as_list(vector: Any) -> list[float]:
        values = vector.tolist() if hasattr(vector, "tolist") else list(vector)
        return [float(value) for value in values]
