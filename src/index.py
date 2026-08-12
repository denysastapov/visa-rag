import json

import numpy as np

from config import CHUNKS_PATH, STORAGE_DIR, VECTORS_PATH


def save_index(chunks: list[dict], vectors: list[list[float]]) -> None:
    STORAGE_DIR.mkdir(exist_ok=True)
    np.save(VECTORS_PATH, np.array(vectors, dtype="float32"))
    CHUNKS_PATH.write_text(json.dumps(chunks, ensure_ascii=False), encoding="utf-8")


def load_index() -> tuple[list[dict], np.ndarray]:
    vectors = np.load(VECTORS_PATH)
    chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
    return chunks, vectors


def search(query_vector, chunks, vectors, top_k=5) -> list[tuple[dict, float]]:
    query = np.array(query_vector, dtype="float32")
    query = query / np.linalg.norm(query)

    matrix = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
    scores = matrix @ query

    best = np.argsort(-scores)[:top_k]
    return [(chunks[i], float(scores[i])) for i in best]
