from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent

DATA_DIR = ROOT / "data" / "raw"

CHUNK_SIZE = 2000
CHUNK_OVERLAP = 200

TOP_K = 8

EMBEDDING_MODEL = "voyage-4"
CHAT_MODEL = "claude-haiku-4-5-20251001"

EMBED_BATCH_SIZE = 16
EMBED_DELAY = 60

STORAGE_DIR = ROOT / "storage"
VECTORS_PATH = STORAGE_DIR / "vectors.npy"
CHUNKS_PATH = STORAGE_DIR / "chunks.json"
QUERY_CACHE_PATH = STORAGE_DIR / "query_cache.json"
