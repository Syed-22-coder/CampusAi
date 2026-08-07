from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Configuration
    API_TITLE: str = "CampusAI API"
    API_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True

    # CORS Configuration
    FRONTEND_URL: str = "http://localhost:3000"
    ALLOWED_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8000"]
    )

    # LLM Configuration
    LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:3b-instruct"
    OLLAMA_TIMEOUT_SECONDS: float = 180.0
    OLLAMA_TEMPERATURE: float = 0.2
    OLLAMA_MAX_TOKENS: int = 500
    OPENAI_API_KEY: Optional[str] = None

    # Vector Database Configuration
    CHROMA_DB_PATH: str = "./chromadb_data"
    CHROMA_COLLECTION_NAME: str = "centennial_knowledge_base"

    # Knowledge Base Configuration
    KNOWLEDGE_BASE_PATH: str = "../knowledge"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 700
    CHUNK_OVERLAP: int = 120
    RETRIEVAL_K: int = 4

    # Environment
    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    @property
    def backend_dir(self) -> Path:
        return BACKEND_DIR

    @property
    def project_root(self) -> Path:
        return BACKEND_DIR.parent

    def resolve_path(self, path_value: str) -> Path:
        candidate = Path(path_value)
        if candidate.is_absolute():
            return candidate
        return (BACKEND_DIR / candidate).resolve()

    @property
    def chroma_db_dir(self) -> Path:
        return self.resolve_path(self.CHROMA_DB_PATH)

    @property
    def knowledge_base_dir(self) -> Path:
        return self.resolve_path(self.KNOWLEDGE_BASE_PATH)


settings = Settings()
