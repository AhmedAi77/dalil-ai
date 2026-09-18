"""Local Whisper transcription that feeds the existing RAG service."""

from pathlib import Path
from typing import Any


class SpeechServiceError(RuntimeError):
    """Raised when local transcription fails."""


class SpeechService:
    def __init__(
        self,
        model_name: str,
        *,
        device: str = "cpu",
        compute_type: str = "int8",
        model: Any | None = None,
    ) -> None:
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self._model = model

    @property
    def model(self) -> Any:
        if self._model is None:
            try:
                from faster_whisper import WhisperModel

                self._model = WhisperModel(
                    self.model_name,
                    device=self.device,
                    compute_type=self.compute_type,
                )
            except Exception as exc:
                raise SpeechServiceError("Could not load the Whisper model") from exc
        return self._model

    def transcribe(self, audio_path: str | Path) -> tuple[str, str | None]:
        path = Path(audio_path)
        if not path.is_file():
            raise FileNotFoundError(f"Audio file not found: {path}")
        try:
            segments, info = self.model.transcribe(str(path), vad_filter=True)
            text = " ".join(segment.text.strip() for segment in segments).strip()
            if not text:
                raise SpeechServiceError("Whisper produced an empty transcription")
            return text, getattr(info, "language", None)
        except SpeechServiceError:
            raise
        except Exception as exc:
            raise SpeechServiceError("Audio transcription failed") from exc
