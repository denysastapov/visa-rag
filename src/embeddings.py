import time

import voyageai

from config import EMBED_BATCH_SIZE, EMBED_DELAY, EMBEDDING_MODEL

_client = voyageai.Client()


def embed_documents(
    texts: list[str],
    batch_size: int = EMBED_BATCH_SIZE,
    delay: int = EMBED_DELAY,
) -> list[list[float]]:
    vectors = []
    total = len(texts)

    for start in range(0, total, batch_size):
        batch = texts[start : start + batch_size]
        response = _client.embed(batch, model=EMBEDDING_MODEL, input_type="document")
        vectors.extend(response.embeddings)

        done = min(start + batch_size, total)
        print(f"      {done}/{total}")

        if delay and done < total:
            time.sleep(delay)

    return vectors


def embed_query(question: str) -> list[float]:
    response = _client.embed([question], model=EMBEDDING_MODEL, input_type="query")
    return response.embeddings[0]
