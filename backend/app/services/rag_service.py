import asyncio
from typing import Iterable, List, Dict, Optional, Sequence, Tuple

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain.chains import ConversationalRetrievalChain, RetrievalQA
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

from config import settings
from app.services.knowledge_loader import KnowledgeLoader
from app.services.llm_service import LLMService
from app.services.prompts import CHAT_QA_PROMPT, CONDENSE_QUESTION_PROMPT, QA_PROMPT
from app.utils.exceptions import KnowledgeBaseError, LLMError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RAGService:
    """Retrieval Augmented Generation Service

    Orchestrates document retrieval from ChromaDB and response generation via LLM
    """

    def __init__(
        self,
        chroma_db=None,
        llm_service: Optional[LLMService] = None,
        embeddings=None,
        knowledge_loader: Optional[KnowledgeLoader] = None,
    ):
        """
        Initialize RAG service

        Args:
            chroma_db: ChromaDB instance (to be injected when ready)
            llm_service: LLM service instance
        """
        self.vectorstore = chroma_db
        self.llm_service = llm_service or LLMService()
        self.embeddings = embeddings
        self.knowledge_loader = knowledge_loader or KnowledgeLoader(embeddings=embeddings)
        self.query_chain = None
        self.chat_chain = None
        self.retriever = None
        self.logger = logger

    async def retrieve_context(
        self,
        query: str,
        k: int = 3
    ) -> Tuple[str, List[Dict]]:
        """
        Retrieve relevant context from knowledge base

        Args:
            query: User query
            k: Number of top results to retrieve

        Returns:
            Tuple of (context_text, sources_list)
        """
        try:
            self.logger.info(f"Retrieving context for query: {query[:50]}")
            if not self._ensure_vectorstore_ready():
                return "", []

            scored_documents = self._similarity_search(query, k)
            if not scored_documents:
                return "", []

            context = "\n\n".join(document.page_content for document, _ in scored_documents)
            sources = self._build_sources_from_scored_documents(scored_documents)
            return context, sources
        except Exception as e:
            self.logger.error(f"Context retrieval error: {str(e)}")
            return "", []

    async def query(
        self,
        query: str,
        context: Optional[str] = None,
        k: int = 3
    ) -> Tuple[str, List[Dict], float]:
        """
        Process query through RAG pipeline

        Args:
            query: User query
            context: Optional additional context
            k: Number of documents to retrieve

        Returns:
            Tuple of (answer, sources, confidence_score)
        """
        try:
            self.logger.info(f"Processing query: {query[:50]}")
            if not self._ensure_vectorstore_ready():
                return (
                    "The knowledge base is not indexed yet. Run the knowledge loader and try again.",
                    [],
                    0.0,
                )

            full_query = query if not context else f"{query}\n\nStudent context: {context}"
            _, sources = await self.retrieve_context(full_query, k)

            if not await self.llm_service.is_available():
                return (
                    "I found relevant Centennial College information, but the local Ollama model is not available right now. Start Ollama and try again.",
                    sources,
                    self._calculate_confidence(sources),
                )

            result = await asyncio.to_thread(self._get_query_chain().invoke, {"query": full_query})
            answer = result.get("result", "").strip()
            source_documents = result.get("source_documents", [])
            if source_documents:
                sources = self._build_sources_from_documents(source_documents)

            confidence = self._calculate_confidence(sources)
            self.logger.info(f"Query processed with confidence: {confidence}")
            return answer, sources, confidence
        except LLMError as exc:
            self.logger.warning(f"LLM unavailable during query: {str(exc)}")
            _, sources = await self.retrieve_context(query, k)
            return (
                "I found relevant Centennial College documents, but the local Ollama model could not generate a response right now.",
                sources,
                self._calculate_confidence(sources),
            )
        except Exception as e:
            self.logger.error(f"Query processing error: {str(e)}")
            raise

    async def initialize_knowledge_base(self, knowledge_path: str) -> bool:
        """
        Initialize knowledge base from files

        Args:
            knowledge_path: Path to knowledge base directory

        Returns:
            Success status
        """
        try:
            self.logger.info(f"Initializing knowledge base from: {knowledge_path}")
            loader = KnowledgeLoader(
                knowledge_path=knowledge_path,
                persist_directory=self._persist_directory(),
                collection_name=self._collection_name(),
                embeddings=self._get_embeddings(),
            )
            await asyncio.to_thread(loader.index_knowledge_base, True)
            self.vectorstore = None
            self.retriever = None
            self.query_chain = None
            self.chat_chain = None
            self.logger.info("Knowledge base initialized")
            return True
        except Exception as e:
            self.logger.error(f"Knowledge base initialization error: {str(e)}")
            return False

    async def chat(
        self,
        message: str,
        chat_history: Optional[Sequence[Tuple[str, str]]] = None,
        k: int = settings.RETRIEVAL_K,
    ) -> Tuple[str, List[Dict], float]:
        if not self._ensure_vectorstore_ready():
            return (
                "The knowledge base is not indexed yet. Run the knowledge loader and try again.",
                [],
                0.0,
            )

        _, sources = await self.retrieve_context(message, k)
        if not await self.llm_service.is_available():
            return (
                "I found relevant Centennial College information, but the local Ollama model is not available right now. Start Ollama and try again.",
                sources,
                self._calculate_confidence(sources),
            )

        result = await asyncio.to_thread(
            self._get_chat_chain().invoke,
            {"question": message, "chat_history": list(chat_history or [])},
        )
        answer = result.get("answer", "").strip()
        source_documents = result.get("source_documents", [])
        if source_documents:
            sources = self._build_sources_from_documents(source_documents)

        confidence = self._calculate_confidence(sources)
        return answer, sources, confidence

    def _get_embeddings(self):
        if self.embeddings is None:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=settings.EMBEDDING_MODEL,
                encode_kwargs={"normalize_embeddings": True},
            )
        return self.embeddings

    def _build_vectorstore(self):
        self.vectorstore = Chroma(
            client=chromadb.PersistentClient(
                path=str(self._persist_directory()),
                settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
            ),
            persist_directory=str(self._persist_directory()),
            collection_name=self._collection_name(),
            embedding_function=self._get_embeddings(),
        )
        self.retriever = None
        self.query_chain = None
        self.chat_chain = None
        return self.vectorstore

    def _ensure_vectorstore_ready(self) -> bool:
        if self.vectorstore is None:
            self._build_vectorstore()

        if self._collection_count() > 0:
            return True

        try:
            self.logger.info("Chroma collection empty, indexing knowledge base now")
            self.knowledge_loader.embeddings = self._get_embeddings()
            self.knowledge_loader.persist_directory = self._persist_directory()
            self.knowledge_loader.collection_name = self._collection_name()
            self.knowledge_loader.index_knowledge_base(reset_collection=False)
            self._build_vectorstore()
            return self._collection_count() > 0
        except Exception as exc:
            self.logger.error(f"Failed to initialize Chroma collection: {exc}")
            return False

    def _collection_count(self) -> int:
        collection = getattr(self.vectorstore, "_collection", None)
        if collection is None:
            return 0
        return int(collection.count())

    def _get_retriever(self):
        if self.retriever is None:
            if not self._ensure_vectorstore_ready():
                raise KnowledgeBaseError("Vector store is not ready for retrieval.")
            self.retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": settings.RETRIEVAL_K},
            )
        return self.retriever

    def _get_query_chain(self):
        if self.query_chain is None:
            self.query_chain = RetrievalQA.from_chain_type(
                llm=self.llm_service.get_langchain_llm(),
                chain_type="stuff",
                retriever=self._get_retriever(),
                return_source_documents=True,
                chain_type_kwargs={"prompt": QA_PROMPT},
            )
        return self.query_chain

    def _get_chat_chain(self):
        if self.chat_chain is None:
            self.chat_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm_service.get_langchain_llm(),
                retriever=self._get_retriever(),
                return_source_documents=True,
                condense_question_prompt=CONDENSE_QUESTION_PROMPT,
                combine_docs_chain_kwargs={"prompt": CHAT_QA_PROMPT},
            )
        return self.chat_chain

    def _similarity_search(self, query: str, k: int) -> List[Tuple]:
        try:
            scored_documents = self.vectorstore.similarity_search_with_score(query, k=k)
            normalized_documents = []
            for document, score in scored_documents:
                if score is None:
                    normalized_documents.append((document, None))
                    continue
                safe_score = max(float(score), 0.0)
                relevance = 1.0 / (1.0 + safe_score)
                normalized_documents.append((document, relevance))
            return normalized_documents
        except Exception:
            documents = self.vectorstore.similarity_search(query, k=k)
            return [(document, None) for document in documents]

    def _build_sources_from_scored_documents(self, scored_documents: Iterable[Tuple]) -> List[Dict]:
        sources: List[Dict] = []
        seen = set()
        for document, relevance in scored_documents:
            source = self._document_to_source(document, relevance)
            source_key = (source["title"], source.get("section"), source.get("source_path"))
            if source_key in seen:
                continue
            seen.add(source_key)
            sources.append(source)
        return sources

    def _build_sources_from_documents(self, documents: Iterable) -> List[Dict]:
        sources: List[Dict] = []
        seen = set()
        for document in documents:
            source = self._document_to_source(document, None)
            source_key = (source["title"], source.get("section"), source.get("source_path"))
            if source_key in seen:
                continue
            seen.add(source_key)
            sources.append(source)
        return sources

    def _document_to_source(self, document, relevance: Optional[float]) -> Dict:
        metadata = getattr(document, "metadata", {}) or {}
        excerpt = " ".join(getattr(document, "page_content", "").split())
        excerpt = excerpt[:260] + ("..." if len(excerpt) > 260 else "")

        source = {
            "title": metadata.get("title") or metadata.get("section") or "Knowledge Base Source",
            "excerpt": excerpt,
            "section": metadata.get("section"),
            "source_path": metadata.get("source_path"),
            "url": metadata.get("source_url"),
        }
        if relevance is not None:
            source["relevance"] = max(0.0, min(1.0, float(relevance)))
        return source

    def _calculate_confidence(self, sources: List[Dict]) -> float:
        if not sources:
            return 0.0
        relevance_values = [
            float(source["relevance"])
            for source in sources
            if source.get("relevance") is not None
        ]
        if relevance_values:
            average_relevance = sum(relevance_values) / len(relevance_values)
            return round(max(0.0, min(1.0, average_relevance)), 2)
        return 0.75

    def _persist_directory(self):
        if self.knowledge_loader and getattr(self.knowledge_loader, "persist_directory", None):
            return self.knowledge_loader.persist_directory
        return settings.chroma_db_dir

    def _collection_name(self) -> str:
        if self.knowledge_loader and getattr(self.knowledge_loader, "collection_name", None):
            return self.knowledge_loader.collection_name
        return settings.CHROMA_COLLECTION_NAME
