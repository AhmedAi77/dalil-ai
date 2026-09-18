"""Direct, deterministic text chunking without a RAG framework."""

from app.models.chunk import DocumentChunk


class Chunker:
    """Split text into overlapping, size-bounded character chunks."""

    def __init__(self, chunk_size: int = 1000, overlap: int = 150) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must be non-negative and smaller than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split(
        self, text: str, *, document_id: str, filename: str
    ) -> list[DocumentChunk]:
        """Create stable `document_id:chunk_index` chunks."""

        content = text.strip()
        if not content:
            return []

        chunks: list[DocumentChunk] = []
        start = 0
        index = 0
        while start < len(content):
            hard_end = min(start + self.chunk_size, len(content))
            end = self._natural_boundary(content, start, hard_end)
            chunk_text = content[start:end].strip()
            if chunk_text:
                chunks.append(
                    DocumentChunk(
                        id=f"{document_id}:{index}",
                        document_id=document_id,
                        filename=filename,
                        chunk_index=index,
                        text=chunk_text,
                        character_count=len(chunk_text),
                    )
                )
                index += 1
            if end >= len(content):
                break
            next_start = max(0, end - self.overlap)
            if next_start <= start:
                next_start = end
            start = next_start
        return chunks

    @staticmethod
    def _natural_boundary(text: str, start: int, hard_end: int) -> int:
        if hard_end >= len(text):
            return len(text)
        search_start = start + ((hard_end - start) // 2)
        for separator in ("\n\n", "\n", ". ", " "):
            boundary = text.rfind(separator, search_start, hard_end)
            if boundary != -1:
                return boundary + len(separator)
        return hard_end
