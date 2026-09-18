from pathlib import Path
from types import SimpleNamespace

from app.services.speech_service import SpeechService


class FakeWhisper:
    def transcribe(self, path, vad_filter=True):
        return iter([SimpleNamespace(text=" How do I "), SimpleNamespace(text=" restart it? ")]), SimpleNamespace(language="en")


def test_transcription_is_exposed(tmp_path: Path) -> None:
    audio = tmp_path / "question.wav"
    audio.write_bytes(b"fake audio")
    service = SpeechService("fake", model=FakeWhisper())

    text, language = service.transcribe(audio)

    assert text == "How do I restart it?"
    assert language == "en"
