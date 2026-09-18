"""Semantic retrieval independent from answer generation."""

from app.models.chunk import RetrievedChunk
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import PineconeVectorStore


class RetrievalService:
    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: PineconeVectorStore,
        *,
        default_top_k: int = 5,
        min_score: float | None = None,
    ) -> None:
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.default_top_k = default_top_k
        self.min_score = min_score

    def retrieve(
        self,
        question: str,
        *,
        top_k: int | None = None,
        document_id: str | None = None,
        user_id: str | None = None,
    ) -> list[RetrievedChunk]:
        if not question.strip():
            raise ValueError("Question cannot be empty")
        vector = self.embedding_service.embed_text(question)
        results = self.vector_store.search(
            vector,
            top_k=top_k or self.default_top_k,
            document_id=document_id,
            user_id=user_id,
        )
        if self.min_score is None:
            return results
        return [result for result in results if result.score >= self.min_score]
