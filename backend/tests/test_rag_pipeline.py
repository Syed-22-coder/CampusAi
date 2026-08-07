import asyncio
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.llms import LLM

from app.services.knowledge_loader import KnowledgeLoader
from app.services.rag_service import RAGService


class KeywordEmbeddings(Embeddings):
    def __init__(self):
        self.keywords = ["progress", "campus", "admissions", "engineering", "services"]

    def embed_documents(self, texts):
        return [self._embed(text) for text in texts]

    def embed_query(self, text):
        return self._embed(text)

    def _embed(self, text):
        lower_text = text.lower()
        return [1.0 if keyword in lower_text else 0.0 for keyword in self.keywords]


class StaticCampusAnswerLLM(LLM):
    @property
    def _llm_type(self) -> str:
        return "static-campus-answer"

    @property
    def _identifying_params(self):
        return {}

    def _call(self, prompt, stop=None, run_manager=None, **kwargs):
        if "progress campus" in prompt.lower():
            return "Progress Campus is located at 941 Progress Ave., Scarborough, ON M1G 3T8."
        return "Admissions questions are handled by Enrolment Services."


class StubLLMService:
    def __init__(self, available=True):
        self.available = available
        self.llm = StaticCampusAnswerLLM()

    async def is_available(self):
        return self.available

    def get_langchain_llm(self, temperature=0.2, max_tokens=500):
        return self.llm


def write_sample_knowledge_base(knowledge_dir: Path):
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    (knowledge_dir / "departments").mkdir(exist_ok=True)
    (knowledge_dir / "facilities").mkdir(exist_ok=True)

    (knowledge_dir / "departments" / "admissions.md").write_text(
        """---
title: Admissions Services
source_url: https://www.centennialcollege.ca/admissions/
---
# Admissions Services

Admissions / Enrolment Services handles applications, transcripts, and registration support.
""",
        encoding="utf-8",
    )

    (knowledge_dir / "facilities" / "progress_campus.md").write_text(
        """---
title: Progress Campus
source_url: https://www.centennialcollege.ca/campuses/progress/
---
# Progress Campus

Progress Campus is located at 941 Progress Ave., Scarborough, ON M1G 3T8.
""",
        encoding="utf-8",
    )


def test_knowledge_loader_indexes_documents(tmp_path):
    knowledge_dir = tmp_path / "knowledge"
    chroma_dir = tmp_path / "chromadb"
    write_sample_knowledge_base(knowledge_dir)

    loader = KnowledgeLoader(
        knowledge_path=knowledge_dir,
        persist_directory=chroma_dir,
        collection_name="test_collection",
        embeddings=KeywordEmbeddings(),
        chunk_size=300,
        chunk_overlap=30,
    )

    result = loader.index_knowledge_base(reset_collection=True)

    assert result["documents_processed"] >= 2
    assert result["chunks_indexed"] >= 2
    assert result["total_chunks_in_collection"] >= 2


def test_rag_query_returns_answer_and_sources(tmp_path):
    knowledge_dir = tmp_path / "knowledge"
    chroma_dir = tmp_path / "chromadb"
    write_sample_knowledge_base(knowledge_dir)

    embeddings = KeywordEmbeddings()
    loader = KnowledgeLoader(
        knowledge_path=knowledge_dir,
        persist_directory=chroma_dir,
        collection_name="test_collection",
        embeddings=embeddings,
        chunk_size=300,
        chunk_overlap=30,
    )
    loader.index_knowledge_base(reset_collection=True)

    rag_service = RAGService(
        llm_service=StubLLMService(available=True),
        embeddings=embeddings,
        knowledge_loader=loader,
    )
    rag_service.knowledge_loader = loader
    rag_service.vectorstore = None

    answer, sources, confidence = asyncio.run(
        rag_service.query("Where is Progress Campus?", None, 3)
    )

    assert answer
    assert "Progress Campus" in answer
    assert sources
    assert sources[0]["title"]
    assert confidence > 0


def test_rag_degrades_gracefully_when_ollama_unavailable(tmp_path):
    knowledge_dir = tmp_path / "knowledge"
    chroma_dir = tmp_path / "chromadb"
    write_sample_knowledge_base(knowledge_dir)

    embeddings = KeywordEmbeddings()
    loader = KnowledgeLoader(
        knowledge_path=knowledge_dir,
        persist_directory=chroma_dir,
        collection_name="test_collection",
        embeddings=embeddings,
        chunk_size=300,
        chunk_overlap=30,
    )
    loader.index_knowledge_base(reset_collection=True)

    rag_service = RAGService(
        llm_service=StubLLMService(available=False),
        embeddings=embeddings,
        knowledge_loader=loader,
    )
    rag_service.knowledge_loader = loader
    rag_service.vectorstore = None

    answer, sources, confidence = asyncio.run(
        rag_service.query("Where is Progress Campus?", None, 3)
    )

    assert "Ollama model is not available" in answer
    assert sources
    assert confidence > 0
