from app.models.chunk import DocumentChunk
from app.services.embedding_service import EmbeddingService


class FakeModel:
    def get_sentence_embedding_dimension(self) -> int:
        return 3

    def encode(self, value, normalize_embeddings=True):
        if isinstance(value, list):
            return [[1, 0, index] for index, _ in enumerate(value)]
        return [0.1, 0.2, 0.3]


def test_embedding_shape_and_batch() -> None:
    service = EmbeddingService("fake", model=FakeModel())
    chunk = DocumentChunk(
        id="d:0",
        document_id="d",
        filename="d.txt",
        chunk_index=0,
        text="hello",
        character_count=5,
    )

    assert service.dimension == 3
    assert service.embed_text("hello") == [0.1, 0.2, 0.3]
    assert service.embed_documents([chunk]) == [[1.0, 0.0, 0.0]]
