"""Thin document-management routes."""

from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.errors import to_http_exception
from app.container import AppContainer, get_container
from app.dependencies.auth import require_user
from app.models.user import UserRecord
from app.models.document import DocumentRecord
from app.schemas.document import DeleteResponse, DocumentResponse, TextDocumentRequest

router = APIRouter(prefix="/documents", tags=["documents"])


def _response(record: DocumentRecord) -> DocumentResponse:
    return DocumentResponse.model_validate(record, from_attributes=True)


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: Annotated[
        UploadFile, File(description="TXT, Markdown, PDF, DOCX, XLSX, or XLSM document")
    ],
    title: Annotated[str, Form(min_length=1, max_length=200)],
    user: Annotated[UserRecord, Depends(require_user)],
    container: Annotated[AppContainer, Depends(get_container)],
) -> DocumentResponse:
    original_name = Path(file.filename or "upload").name
    extension = Path(original_name).suffix.lower()
    if extension not in container.processor.supported_extensions:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {extension}")
    contents = await file.read(container.settings.max_upload_bytes + 1)
    if len(contents) > container.settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Uploaded file is too large")
    stored_path = container.settings.upload_dir / f"{uuid4().hex}_{original_name}"
    try:
        stored_path.write_bytes(contents)
        return _response(
            container.ingestion.ingest_path(
                str(stored_path), title=title, user_id=user.id
            )
        )
    except Exception as exc:
        stored_path.unlink(missing_ok=True)
        raise to_http_exception(exc) from exc
    finally:
        await file.close()


@router.post("/text", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def ingest_text(
    request: TextDocumentRequest,
    user: Annotated[UserRecord, Depends(require_user)],
    container: Annotated[AppContainer, Depends(get_container)],
) -> DocumentResponse:
    try:
        return _response(
            container.ingestion.ingest_text(
                request.text, title=request.title, user_id=user.id
            )
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    user: Annotated[UserRecord, Depends(require_user)],
    container: Annotated[AppContainer, Depends(get_container)],
) -> list[DocumentResponse]:
    return [
        _response(record) for record in container.repository.list(user_id=user.id)
    ]


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    user: Annotated[UserRecord, Depends(require_user)],
    container: Annotated[AppContainer, Depends(get_container)],
) -> DocumentResponse:
    try:
        return _response(
            container.repository.require(document_id, user_id=user.id)
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.delete("/{document_id}", response_model=DeleteResponse)
def delete_document(
    document_id: str,
    user: Annotated[UserRecord, Depends(require_user)],
    container: Annotated[AppContainer, Depends(get_container)],
) -> DeleteResponse:
    try:
        deleted = container.ingestion.delete(document_id, user_id=user.id)
        return DeleteResponse(deleted=deleted, document_id=document_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc
