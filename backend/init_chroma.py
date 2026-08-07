import chromadb
from chromadb.config import Settings as ChromaSettings
from config import settings

settings.chroma_db_dir.mkdir(parents=True, exist_ok=True)
client = chromadb.PersistentClient(
    path=str(settings.chroma_db_dir),
    settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
)

collection = client.get_or_create_collection(name=settings.CHROMA_COLLECTION_NAME)

print(f"Chroma Database initialized at {settings.chroma_db_dir}")
