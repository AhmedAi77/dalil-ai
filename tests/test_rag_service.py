from app.models.chunk import RetrievedChunk
from app.services.context_builder import ContextBuilder
from app.services.rag_service import NO_ANSWER, RAGService


class FakeRetrieval:
    def __init__(self, chunks):
        self.chunks = chunks
        self.question = ""

    def retrieve(self, question, *, top_k=None, document_id=None, user_id=None):
        self.question = question
        return self.chunks


class FakeLLM:
    def __init__(self):
        self.context = ""

    def generate(self, question, context):
        self.context = context
        return "Restart the service [Source 1]."

    def translate_for_retrieval(self, question):
        return "What does gg.txt contain?"


def test_no_retrieval_has_deterministic_no_answer() -> None:
    llm = FakeLLM()
    service = RAGService(FakeRetrieval([]), ContextBuilder(), llm)

    result = service.answer("Capital of Japan?")

    assert result.answer == NO_ANSWER
    assert result.sources == []
    assert llm.context == ""


def test_answer_preserves_sources() -> None:
    chunk = RetrievedChunk(
        id="d:2",
        document_id="d",
        filename="docker.txt",
        chunk_index=2,
        text="Restart the Docker service.",
        character_count=27,
        score=0.88,
    )
    llm = FakeLLM()
    service = RAGService(FakeRetrieval([chunk]), ContextBuilder(), llm)

    result = service.answer("What should I restart?")

    assert result.sources[0].chunk_index == 2
    assert "[Source 1: docker.txt" in llm.context


def test_arabic_question_is_translated_for_retrieval_but_kept_for_answer() -> None:
    chunk = RetrievedChunk(
        id="d:0", document_id="d", filename="gg.txt", chunk_index=0,
        text="The file contains a release checklist.", character_count=38,
        score=0.9,
    )
    retrieval = FakeRetrieval([chunk])
    llm = FakeLLM()
    service = RAGService(retrieval, ContextBuilder(), llm)

    service.answer("ماذا يحتوي gg.txt؟")

    assert retrieval.question == "What does gg.txt contain?"
    assert "release checklist" in llm.context


def test_arabic_no_answer_is_localized() -> None:
    service = RAGService(FakeRetrieval([]), ContextBuilder(), FakeLLM())

    result = service.answer("ما هي الإجابة؟")

    assert result.answer == "لا تحتوي المستندات المتاحة على معلومات كافية للإجابة عن هذا السؤال."
