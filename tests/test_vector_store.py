import pytest

from app.models.chunk import DocumentChunk
from app.services.vector_store import PineconeVectorStore, VectorStoreError


class FakeIndex:
    def __init__(self) -> None:
        self.upserted = []
        self.deleted_filter = None
        self.query_filter = None

    def upsert(self, *, vectors, namespace):
        self.upserted = vectors

    def query(self, **kwargs):
        self.query_filter = kwargs.get("filter")
        return {
            "matches": [
                {
                    "id": "doc:0",
                    "score": 0.91,
                    "metadata": {
                        "document_id": "doc",
                        "filename": "notes.txt",
                        "chunk_index": 0,
                        "text": "Docker daemon troubleshooting",
                        "character_count": 29,
                    },
                }
            ]
        }

    def delete(self, *, filter, namespace):
        self.deleted_filter = filter


class FakeClient:
    def __init__(self, index: FakeIndex, dimension: int = 3) -> None:
        self.index = index
        self.dimension = dimension

    def has_index(self, name):
        return True

    def describe_index(self, name):
        return {"dimension": self.dimension}

    def Index(self, name):
        return self.index


def build_store(dimension: int = 3) -> tuple[PineconeVectorStore, FakeIndex]:
    index = FakeIndex()
    return (
        PineconeVectorStore(
            api_key="test",
            index_name="test",
            client=FakeClient(index, dimension),
            index=index,
        ),
        index,
    )


def test_vector_traceability_search_and_delete() -> None:
    store, index = build_store()
    chunk = DocumentChunk(
        id="doc:0",
        document_id="doc",
        filename="notes.txt",
        chunk_index=0,
        text="Docker daemon troubleshooting",
        character_count=29,
    )

    store.ensure_index(3)
    store.upsert([chunk], [[1, 0, 0]], user_id="user-1")
    assert index.upserted[0]["metadata"]["document_id"] == "doc"
    assert index.upserted[0]["metadata"]["user_id"] == "user-1"

    result = store.search(
        [1, 0, 0], top_k=1, document_id="doc", user_id="user-1"
    )[0]
    assert result.score == 0.91
    assert result.filename == "notes.txt"
    assert index.query_filter == {
        "$and": [
            {"user_id": {"$eq": "user-1"}},
            {"document_id": {"$eq": "doc"}},
        ]
    }

    store.delete_document("doc", user_id="user-1")
    assert index.deleted_filter == {
        "$and": [
            {"document_id": {"$eq": "doc"}},
            {"user_id": {"$eq": "user-1"}},
        ]
    }


def test_dimension_mismatch_is_rejected() -> None:
    store, _ = build_store(dimension=384)
    with pytest.raises(VectorStoreError, match="does not match"):
        store.ensure_index(768)
