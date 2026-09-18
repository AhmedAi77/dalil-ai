"""Exercise the real embedding, Pinecone, retrieval, and Ollama path safely."""

import time
from pathlib import Path
import sys
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.container import get_container


def main() -> None:
    container = get_container()
    marker = uuid4().hex[:8]
    text = (
        f"Test marker {marker}. The Aurora Wrench protocol requires restarting "
        "the nebula-seven service after checking the amber diagnostic logs."
    )
    record = None
    try:
        print("1. Ingesting temporary document...")
        record = container.ingestion.ingest_text(
            text, title=f"live-smoke-{marker}"
        )
        print(f"   indexed document: {record.id}")

        print("2. Waiting for filtered Pinecone retrieval...")
        chunks = []
        for _ in range(10):
            chunks = container.retrieval.retrieve(
                "What service does the Aurora Wrench protocol restart?",
                document_id=record.id,
                top_k=3,
            )
            if chunks:
                break
            time.sleep(2)
        if not chunks:
            raise RuntimeError("Pinecone did not return the temporary document")
        print(
            f"   retrieved {len(chunks)} chunk(s); "
            f"top score={chunks[0].score:.4f}"
        )

        print("3. Asking local Qwen with retrieved context...")
        response = container.rag.answer(
            "What service does the Aurora Wrench protocol restart?",
            document_id=record.id,
            top_k=3,
        )
        print(f"   answer: {response.answer}")
        print(f"   sources: {len(response.sources)}")
        if "nebula-seven" not in response.answer.lower():
            raise RuntimeError("The grounded answer omitted the expected service")
        print("LIVE SMOKE TEST PASSED")
    finally:
        if record is not None:
            print("4. Removing temporary SQLite record and Pinecone vectors...")
            container.ingestion.delete(record.id)


if __name__ == "__main__":
    main()
