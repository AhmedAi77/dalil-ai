"""Composition root: construct and connect application services in one place."""

from functools import lru_cache

from app.config import Settings, get_settings
from app.database import Database, DocumentRepository
from app.services.chunker import Chunker
from app.services.context_builder import ContextBuilder
from app.services.document_processor import DocumentProcessor
from app.services.embedding_service import EmbeddingService
from app.services.ingestion_service import IngestionService
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.services.retrieval_service import RetrievalService
from app.services.speech_service import SpeechService
from app.services.vector_store import PineconeVectorStore


class AppContainer:
    """Central dependency wiring; services remain independently testable."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.database = Database(settings.database_path)
        self.database.initialize()
        settings.upload_dir.mkdir(parents=True, exist_ok=True)

        self.repository = DocumentRepository(self.database)
        self.processor = DocumentProcessor()
        self.chunker = Chunker(settings.chunk_size, settings.chunk_overlap)
        self.embeddings = EmbeddingService(settings.embedding_model)
        self.vector_store = PineconeVectorStore(
            api_key=settings.pinecone_api_key,
            index_name=settings.pinecone_index_name,
            namespace=settings.pinecone_namespace,
            cloud=settings.pinecone_cloud,
            region=settings.pinecone_region,
        )
        self.ingestion = IngestionService(
            self.processor,
            self.repository,
            self.chunker,
            self.embeddings,
            self.vector_store,
            owned_upload_dir=settings.upload_dir,
        )
        self.retrieval = RetrievalService(
            self.embeddings,
            self.vector_store,
            default_top_k=settings.top_k,
            min_score=settings.retrieval_min_score,
        )
        self.llm = LLMService(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
        )
        self.rag = RAGService(self.retrieval, ContextBuilder(), self.llm)
        self.speech = SpeechService(
            settings.whisper_model,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
        )


@lru_cache(maxsize=1)
def get_container() -> AppContainer:
    return AppContainer(get_settings())
