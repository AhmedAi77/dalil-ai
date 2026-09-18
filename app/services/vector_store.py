"""Pinecone adapter: the only module that knows the Pinecone SDK."""

from collections.abc import Sequence
from typing import Any

from app.models.chunk import DocumentChunk, RetrievedChunk


class VectorStoreError(RuntimeError):
    """Raised for Pinecone setup or operation failures."""


class PineconeVectorStore:
    def __init__(
        self,
        *,
        api_key: str,
        index_name: str,
        namespace: str = "documents",
        cloud: str = "aws",
        region: str = "us-east-1",
        client: Any | None = None,
        index: Any | None = None,
    ) -> None:
        self.api_key = api_key
        self.index_name = index_name
        self.namespace = namespace
        self.cloud = cloud
        self.region = region
        self._client = client
        self._index = index

    def ensure_index(self, dimension: int) -> None:
        """Create an index or reject a dimension mismatch."""

        client = self._get_client()
        try:
            if not client.has_index(self.index_name):
                from pinecone import ServerlessSpec

                client.create_index(
                    name=self.index_name,
                    vector_type="dense",
                    dimension=dimension,
                    metric="cosine",
                    spec=ServerlessSpec(cloud=self.cloud, region=self.region),
                )
            description = client.describe_index(self.index_name)
            actual = self._value(description, "dimension")
            if int(actual) != dimension:
                raise VectorStoreError(
                    f"Pinecone dimension {actual} does not match embedding "
                    f"dimension {dimension}"
                )
            self._index = client.Index(self.index_name)
        except VectorStoreError:
            raise
        except Exception as exc:
            raise VectorStoreError("Could not prepare the Pinecone index") from exc

    def upsert(
        self,
        chunks: Sequence[DocumentChunk],
        vectors: Sequence[Sequence[float]],
        *,
        user_id: str | None = None,
    ) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("Each chunk must have exactly one embedding")
        records = [
            {
                "id": chunk.id,
                "values": list(vector),
                "metadata": {
                    "document_id": chunk.document_id,
                    "filename": chunk.filename,
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                    "character_count": chunk.character_count,
                    "user_id": user_id or "legacy",
                },
            }
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        try:
            self._get_index().upsert(vectors=records, namespace=self.namespace)
        except Exception as exc:
            raise VectorStoreError("Pinecone vector upsert failed") from exc

    def search(
        self,
        vector: Sequence[float],
        *,
        top_k: int,
        document_id: str | None = None,
        user_id: str | None = None,
    ) -> list[RetrievedChunk]:
        conditions: list[dict[str, dict[str, str]]] = []
        if user_id:
            conditions.append({"user_id": {"$eq": user_id}})
        if document_id:
            conditions.append({"document_id": {"$eq": document_id}})
        metadata_filter = (
            conditions[0]
            if len(conditions) == 1
            else {"$and": conditions}
            if conditions
            else None
        )
        try:
            response = self._get_index().query(
                vector=list(vector),
                top_k=top_k,
                include_metadata=True,
                namespace=self.namespace,
                filter=metadata_filter,
            )
            matches = self._value(response, "matches") or []
            results: list[RetrievedChunk] = []
            for match in matches:
                metadata = self._value(match, "metadata") or {}
                text = str(metadata.get("text", "")).strip()
                if not text:
                    continue
                results.append(
                    RetrievedChunk(
                        id=str(self._value(match, "id")),
                        document_id=str(metadata["document_id"]),
                        filename=str(metadata["filename"]),
                        chunk_index=int(metadata["chunk_index"]),
                        text=text,
                        character_count=int(
                            metadata.get("character_count", len(text))
                        ),
                        score=float(self._value(match, "score")),
                    )
                )
            return results
        except Exception as exc:
            raise VectorStoreError("Pinecone similarity search failed") from exc

    def delete_document(
        self, document_id: str, *, user_id: str | None = None
    ) -> None:
        conditions: list[dict[str, dict[str, str]]] = [
            {"document_id": {"$eq": document_id}}
        ]
        if user_id:
            conditions.append({"user_id": {"$eq": user_id}})
        metadata_filter = conditions[0] if len(conditions) == 1 else {"$and": conditions}
        try:
            self._get_index().delete(
                filter=metadata_filter,
                namespace=self.namespace,
            )
        except Exception as exc:
            raise VectorStoreError("Pinecone vector deletion failed") from exc

    def _get_client(self) -> Any:
        if self._client is None:
            if not self.api_key:
                raise VectorStoreError("PINECONE_API_KEY is not configured")
            try:
                from pinecone import Pinecone

                self._client = Pinecone(api_key=self.api_key)
            except Exception as exc:
                raise VectorStoreError("Could not create Pinecone client") from exc
        return self._client

    def _get_index(self) -> Any:
        if self._index is None:
            self._index = self._get_client().Index(self.index_name)
        return self._index

    @staticmethod
    def _value(value: Any, name: str) -> Any:
        return value.get(name) if isinstance(value, dict) else getattr(value, name)
