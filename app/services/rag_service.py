"""RAG orchestration composed from focused services."""

import re

from app.schemas.query import QueryResponse, SourceReference
from app.services.context_builder import ContextBuilder
from app.services.llm_service import LLMService
from app.services.retrieval_service import RetrievalService


NO_ANSWER = (
    "The available documents do not contain enough information to answer "
    "this question."
)
NO_ANSWER_AR = "لا تحتوي المستندات المتاحة على معلومات كافية للإجابة عن هذا السؤال."
ARABIC_PATTERN = re.compile(r"[\u0600-\u06ff]")


class RAGService:
    def __init__(
        self,
        retrieval_service: RetrievalService,
        context_builder: ContextBuilder,
        llm_service: LLMService,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.context_builder = context_builder
        self.llm_service = llm_service

    def answer(
        self,
        question: str,
        *,
        document_id: str | None = None,
        top_k: int | None = None,
        user_id: str | None = None,
    ) -> QueryResponse:
        if not question.strip():
            raise ValueError("Question cannot be empty")
        is_arabic = bool(ARABIC_PATTERN.search(question))
        retrieval_question = question
        if is_arabic:
            try:
                retrieval_question = self.llm_service.translate_for_retrieval(question)
            except Exception:
                # Translation improves cross-language recall, but answering should
                # still work when the optional rewrite request is unavailable.
                retrieval_question = question
        chunks = self.retrieval_service.retrieve(
            retrieval_question,
            top_k=top_k,
            document_id=document_id,
            user_id=user_id,
        )
        if not chunks:
            return QueryResponse(
                answer=NO_ANSWER_AR if is_arabic else NO_ANSWER,
                sources=[],
            )

        context = self.context_builder.build(chunks)
        answer = self.llm_service.generate(question, context)
        sources = [
            SourceReference(
                document_id=chunk.document_id,
                filename=chunk.filename,
                chunk_index=chunk.chunk_index,
                score=chunk.score,
            )
            for chunk in chunks
        ]
        return QueryResponse(answer=answer, sources=sources)
