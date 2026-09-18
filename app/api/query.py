"""Typed-question RAG route."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.errors import to_http_exception
from app.container import AppContainer, get_container
from app.dependencies.auth import require_user
from app.models.user import UserRecord
from app.schemas.query import QueryRequest, QueryResponse

router = APIRouter(tags=["query"])


def _mentioned_document_id(question: str, documents: list) -> str | None:
    """Resolve an explicitly mentioned filename, independent of query language."""
    folded_question = question.casefold()
    matches = [doc for doc in documents if doc.filename.casefold() in folded_question]
    if not matches:
        return None
    return max(matches, key=lambda doc: len(doc.filename)).id


@router.post("/query", response_model=QueryResponse)
def query_documents(
    request: QueryRequest,
    user: Annotated[UserRecord, Depends(require_user)],
    container: Annotated[AppContainer, Depends(get_container)],
) -> QueryResponse:
    try:
        document_id = request.document_id
        if document_id:
            container.repository.require(document_id, user_id=user.id)
        else:
            document_id = _mentioned_document_id(
                request.question,
                container.repository.list(user_id=user.id),
            )
        return container.rag.answer(
            request.question,
            document_id=document_id,
            top_k=request.top_k,
            user_id=user.id,
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc
