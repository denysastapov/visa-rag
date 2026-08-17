from config import RERANK_ENABLED, RERANK_MAX_PER_SOURCE, RERANK_MODEL

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import CrossEncoder

        _model = CrossEncoder(RERANK_MODEL)
    return _model


def _limit_per_source(ranked, top_k, max_per_source):
    kept = []
    overflow = []
    seen: dict[str, int] = {}

    for chunk, score in ranked:
        source = chunk["source"]
        if seen.get(source, 0) < max_per_source:
            seen[source] = seen.get(source, 0) + 1
            kept.append((chunk, score))
        else:
            overflow.append((chunk, score))

    return (kept + overflow)[:top_k]


def rerank(
    question: str,
    candidates: list[tuple[dict, float]],
    top_k: int,
) -> list[tuple[dict, float]]:
    if not RERANK_ENABLED or not candidates:
        return candidates[:top_k]

    pairs = [(question, chunk["text"]) for chunk, _score in candidates]
    scores = _get_model().predict(pairs)

    ranked = sorted(
        ((chunk, float(score)) for (chunk, _), score in zip(candidates, scores)),
        key=lambda pair: pair[1],
        reverse=True,
    )

    if RERANK_MAX_PER_SOURCE:
        return _limit_per_source(ranked, top_k, RERANK_MAX_PER_SOURCE)
    return ranked[:top_k]
