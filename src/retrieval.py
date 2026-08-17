from config import RERANK_CANDIDATES, RERANK_ENABLED, TOP_K
from src.embeddings import embed_query
from src.index import search
from src.rerank import rerank


def retrieve(question: str, chunks, vectors, top_k: int = TOP_K) -> list[tuple[dict, float]]:
    shortlist_size = max(RERANK_CANDIDATES, top_k) if RERANK_ENABLED else top_k
    candidates = search(embed_query(question), chunks, vectors, shortlist_size)
    return rerank(question, candidates, top_k)
