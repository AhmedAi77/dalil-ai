"""Speech input route that reuses the typed RAG pipeline."""

from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.errors import to_http_exception
from app.container import AppContainer, get_container
from app.dependencies.auth import require_user
from app.models.user import UserRecord
from app.schemas.speech import SpeechQueryResponse

router = APIRouter(prefix="/speech", tags=["speech"])


@router.post("/query", response_model=SpeechQueryResponse)
async def speech_query(
    audio: Annotated[UploadFile, File(description="Audio question")],
    user: Annotated[UserRecord, Depends(require_user)],
    container: Annotated[AppContainer, Depends(get_container)],
    document_id: str | None = None,
) -> SpeechQueryResponse:
    suffix = Path(audio.filename or "question.wav").suffix.lower() or ".wav"
    if suffix not in {".wav", ".mp3", ".m4a", ".ogg", ".webm", ".flac"}:
        raise HTTPException(status_code=415, detail="Unsupported audio type")
    audio_dir = container.settings.upload_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    path = audio_dir / f"{uuid4().hex}{suffix}"
    try:
        contents = await audio.read(container.settings.max_upload_bytes + 1)
        if len(contents) > container.settings.max_upload_bytes:
            raise HTTPException(status_code=413, detail="Uploaded audio is too large")
        path.write_bytes(contents)
        transcription, language = container.speech.transcribe(path)
        result = container.rag.answer(
            transcription, document_id=document_id, user_id=user.id
        )
        return SpeechQueryResponse(
            transcription=transcription,
            language=language,
            answer=result.answer,
            sources=result.sources,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise to_http_exception(exc) from exc
    finally:
        path.unlink(missing_ok=True)
        await audio.close()
