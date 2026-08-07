import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from config import settings
from app.utils.exceptions import KnowledgeBaseError
from app.utils.logger import get_logger


logger = get_logger(__name__)
FRONTMATTER_PATTERN = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)
SKIPPED_FILES = {"README.md", ".gitkeep"}


class KnowledgeLoader:
    """Load, chunk, and index Centennial knowledge base files into ChromaDB."""

    def __init__(
        self,
        knowledge_path: Optional[Path | str] = None,
        persist_directory: Optional[Path | str] = None,
        collection_name: Optional[str] = None,
        embeddings=None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ):
        self.knowledge_path = Path(knowledge_path or settings.knowledge_base_dir).resolve()
        self.persist_directory = Path(persist_directory or settings.chroma_db_dir).resolve()
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        self.embeddings = embeddings
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        self.logger = logger

    def _get_embeddings(self):
        if self.embeddings is None:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=settings.EMBEDDING_MODEL,
                encode_kwargs={"normalize_embeddings": True},
            )
        return self.embeddings

    def iter_knowledge_files(self) -> Iterable[Path]:
        for file_path in sorted(self.knowledge_path.rglob("*")):
            if not file_path.is_file():
                continue
            if file_path.name in SKIPPED_FILES or file_path.name.startswith("."):
                continue
            if file_path.suffix.lower() not in {".md", ".json"}:
                continue
            yield file_path

    def load_documents(self) -> List[Document]:
        if not self.knowledge_path.exists():
            raise KnowledgeBaseError(f"Knowledge base path does not exist: {self.knowledge_path}")

        documents: List[Document] = []
        for file_path in self.iter_knowledge_files():
            if file_path.suffix.lower() == ".md":
                documents.extend(self._load_markdown_documents(file_path))
            elif file_path.suffix.lower() == ".json":
                documents.extend(self._load_json_documents(file_path))

        if not documents:
            raise KnowledgeBaseError("No knowledge base documents were loaded for indexing.")

        self.logger.info(
            "Knowledge documents loaded",
            extra={"extra_data": {"documents_loaded": len(documents)}},
        )
        return documents

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        chunks = self.text_splitter.split_documents(documents)
        for index, chunk in enumerate(chunks):
            chunk.metadata = self._sanitize_metadata(dict(chunk.metadata))
            chunk.metadata["chunk_index"] = index
            chunk.metadata["chunk_id"] = self._build_chunk_id(chunk, index)
        return chunks

    def index_knowledge_base(self, reset_collection: bool = False) -> Dict[str, Any]:
        documents = self.load_documents()
        chunks = self.chunk_documents(documents)

        if reset_collection and self.persist_directory.exists():
            shutil.rmtree(self.persist_directory)

        self.persist_directory.mkdir(parents=True, exist_ok=True)
        client = self._create_client()

        if reset_collection:
            try:
                client.reset()
            except Exception:
                pass
            client = self._create_client()

        vectorstore = Chroma(
            client=client,
            collection_name=self.collection_name,
            persist_directory=str(self.persist_directory),
            embedding_function=self._get_embeddings(),
        )

        vectorstore.add_documents(
            chunks,
            ids=[chunk.metadata["chunk_id"] for chunk in chunks],
        )
        if hasattr(vectorstore, "persist"):
            vectorstore.persist()

        total_chunks = getattr(getattr(vectorstore, "_collection", None), "count", lambda: len(chunks))()

        result = {
            "documents_processed": len(documents),
            "chunks_indexed": len(chunks),
            "collection_name": self.collection_name,
            "persist_directory": str(self.persist_directory),
            "total_chunks_in_collection": total_chunks,
        }
        self.logger.info("Knowledge base indexed", extra={"extra_data": result})
        return result

    def _load_markdown_documents(self, file_path: Path) -> List[Document]:
        raw_text = file_path.read_text(encoding="utf-8", errors="replace")
        frontmatter, body = self._parse_frontmatter(raw_text)
        title = frontmatter.get("title") or self._extract_first_heading(body) or self._prettify_name(file_path.stem)
        source_url = frontmatter.get("source_url")
        relative_path = str(file_path.relative_to(self.knowledge_path)).replace("\\", "/")

        sections = self._split_markdown_sections(body)
        documents: List[Document] = []
        for section_title, section_content in sections:
            content = section_content.strip()
            if not content:
                continue
            documents.append(
                Document(
                    page_content=content,
                    metadata={
                        "title": title,
                        "section": section_title,
                        "source_url": source_url,
                        "source_path": relative_path,
                        "file_name": file_path.name,
                    },
                )
            )

        if not documents:
            documents.append(
                Document(
                    page_content=body.strip(),
                    metadata={
                        "title": title,
                        "section": "Overview",
                        "source_url": source_url,
                        "source_path": relative_path,
                        "file_name": file_path.name,
                    },
                )
            )

        return documents

    def _load_json_documents(self, file_path: Path) -> List[Document]:
        raw_text = file_path.read_text(encoding="utf-8", errors="replace")
        payload = json.loads(raw_text)
        relative_path = str(file_path.relative_to(self.knowledge_path)).replace("\\", "/")
        base_title = self._extract_json_title(payload) or self._prettify_name(file_path.stem)

        documents: List[Document] = []
        if isinstance(payload, dict):
            for key, value in payload.items():
                section_title = self._prettify_name(str(key))
                documents.append(
                    Document(
                        page_content=self._json_value_to_text(section_title, value),
                        metadata={
                            "title": base_title,
                            "section": section_title,
                            "source_url": None,
                            "source_path": relative_path,
                            "file_name": file_path.name,
                        },
                    )
                )
        else:
            documents.append(
                Document(
                    page_content=self._json_value_to_text(base_title, payload),
                    metadata={
                        "title": base_title,
                        "section": "Overview",
                        "source_url": None,
                        "source_path": relative_path,
                        "file_name": file_path.name,
                    },
                )
            )

        return documents

    def _parse_frontmatter(self, raw_text: str) -> Tuple[Dict[str, str], str]:
        match = FRONTMATTER_PATTERN.match(raw_text)
        if not match:
            return {}, raw_text

        metadata: Dict[str, str] = {}
        for line in match.group(1).splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip().strip("\"'")
        body = raw_text[match.end():]
        return metadata, body

    def _split_markdown_sections(self, body: str) -> List[Tuple[str, str]]:
        matches = list(HEADING_PATTERN.finditer(body))
        if not matches:
            return [("Overview", body.strip())]

        sections: List[Tuple[str, str]] = []
        intro_text = body[:matches[0].start()].strip()
        if intro_text:
            sections.append(("Overview", intro_text))

        for index, match in enumerate(matches):
            heading = match.group(2).strip()
            start = match.start()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
            section_text = body[start:end].strip()
            if section_text:
                sections.append((heading, section_text))

        return sections

    def _extract_first_heading(self, body: str) -> Optional[str]:
        match = HEADING_PATTERN.search(body)
        if not match:
            return None
        return match.group(2).strip()

    def _extract_json_title(self, payload: Any) -> Optional[str]:
        if not isinstance(payload, dict):
            return None
        institution = payload.get("institution")
        if isinstance(institution, dict):
            name = institution.get("name")
            if isinstance(name, str):
                return name
        return None

    def _json_value_to_text(self, label: str, value: Any, indent: int = 0) -> str:
        prefix = "  " * indent
        if isinstance(value, dict):
            lines = [f"{prefix}{label}:"]
            for key, nested_value in value.items():
                lines.append(self._json_value_to_text(self._prettify_name(str(key)), nested_value, indent + 1))
            return "\n".join(lines)
        if isinstance(value, list):
            lines = [f"{prefix}{label}:"]
            for item in value:
                lines.append(self._json_value_to_text("- item", item, indent + 1))
            return "\n".join(lines)
        return f"{prefix}{label}: {value}"

    def _build_chunk_id(self, chunk: Document, index: int) -> str:
        seed = "|".join(
            [
                str(chunk.metadata.get("source_path", "")),
                str(chunk.metadata.get("section", "")),
                str(index),
                chunk.page_content[:120],
            ]
        )
        return hashlib.sha1(seed.encode("utf-8")).hexdigest()

    def _prettify_name(self, raw_name: str) -> str:
        normalized = raw_name.replace("_", " ").replace("-", " ")
        normalized = re.sub(r"\s*\(\d+\)$", "", normalized)
        return normalized.strip().title()

    def _sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        sanitized: Dict[str, Any] = {}
        for key, value in metadata.items():
            if value is None:
                continue
            if isinstance(value, (str, int, float, bool)):
                sanitized[key] = value
            else:
                sanitized[key] = str(value)
        return sanitized

    def _create_client(self):
        return chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )


def main():
    parser = argparse.ArgumentParser(description="Index the CampusAI knowledge base into ChromaDB.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete the existing collection before re-indexing.",
    )
    args = parser.parse_args()

    loader = KnowledgeLoader()
    result = loader.index_knowledge_base(reset_collection=args.reset)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
