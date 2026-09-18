import pytest

from app.services.chunker import Chunker


def test_chunks_are_bounded_stable_and_overlapping() -> None:
    chunks = Chunker(chunk_size=10, overlap=3).split(
        "abcdefghijklmnopqrstuvwxyz", document_id="doc-1", filename="letters.txt"
    )

    assert [chunk.id for chunk in chunks] == [
        "doc-1:0",
        "doc-1:1",
        "doc-1:2",
        "doc-1:3",
    ]
    assert all(chunk.character_count <= 10 for chunk in chunks)
    assert chunks[0].text[-3:] == chunks[1].text[:3]


def test_invalid_overlap_is_rejected() -> None:
    with pytest.raises(ValueError):
        Chunker(chunk_size=100, overlap=100)
