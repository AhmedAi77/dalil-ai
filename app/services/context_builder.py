"""Convert only retrieved chunks into explicit LLM context."""

from collections.abc import Sequence

from app.models.chunk import RetrievedChunk


class ContextBuilder:
    def build(self, chunks: Sequence[RetrievedChunk]) -> str:
        sections = [
            (
                f"[Source {position}: {chunk.filename}, "
                f"document_id={chunk.document_id}, chunk={chunk.chunk_index}]\n"
                f"{chunk.text}"
            )
            for position, chunk in enumerate(chunks, start=1)
        ]
        return "\n\n---\n\n".join(sections)
