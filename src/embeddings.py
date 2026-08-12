import json
import time

import voyageai

from config import (
    EMBED_BATCH_SIZE,
    EMBED_DELAY,
    EMBEDDING_MODEL,
    QUERY_CACHE_PATH,
    STORAGE_DIR,
)

_client = voyageai.Client()

RATE_LIMIT_WAIT = 25
MAX_ATTEMPTS = 4


def _embed(texts: list[str], input_type: str) -> list[list[float]]:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = _client.embed(texts, model=EMBEDDING_MODEL, input_type=input_type)
            return response.embeddings
        except voyageai.error.RateLimitError:
            if attempt == MAX_ATTEMPTS:
                raise
            print(f"      rate limited, waiting {RATE_LIMIT_WAIT}s")
            time.sleep(RATE_LIMIT_WAIT)
    raise RuntimeError("unreachable")


def embed_documents(
    texts: list[str],
    batch_size: int = EMBED_BATCH_SIZE,
    delay: int = EMBED_DELAY,
) -> list[list[float]]:
    vectors = []
    total = len(texts)

    for start in range(0, total, batch_size):
        vectors.extend(_embed(texts[start : start + batch_size], "document"))

        done = min(start + batch_size, total)
        print(f"      {done}/{total}")

        if delay and done < total:
            time.sleep(delay)

    return vectors


def _load_query_cache() -> dict:
    if QUERY_CACHE_PATH.exists():
        return json.loads(QUERY_CACHE_PATH.read_text(encoding="utf-8"))
    return {}


_query_cache = _load_query_cache()


def embed_query(question: str) -> list[float]:
    key = f"{EMBEDDING_MODEL}::{question}"
    if key in _query_cache:
        return _query_cache[key]

    vector = _embed([question], "query")[0]

    _query_cache[key] = vector
    STORAGE_DIR.mkdir(exist_ok=True)
    QUERY_CACHE_PATH.write_text(json.dumps(_query_cache), encoding="utf-8")
    return vector
