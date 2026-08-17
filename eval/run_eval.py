import json
import sys
from datetime import date

from config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    EVAL_RESULTS_PATH,
    RERANK_ENABLED,
    RERANK_MODEL,
    STORAGE_DIR,
    TOP_K,
)
from eval.questions import ANSWERABLE, CROSS_LINGUAL, MUST_REFUSE, REFUSAL_MARKERS
from src.generate import answer
from src.index import load_index
from src.retrieval import retrieve

OK = "PASS"
BAD = "FAIL"


def _label(expect_source):
    if isinstance(expect_source, str):
        return expect_source
    return " | ".join(expect_source)


def rank_of_expected(results, expect_source):
    accepted = [expect_source] if isinstance(expect_source, str) else expect_source
    for position, (chunk, _score) in enumerate(results, start=1):
        if any(name.lower() in chunk["source"].lower() for name in accepted):
            return position
    return None


def run_retrieval(chunks, vectors):
    print(f"\nRETRIEVAL  chunk_size={CHUNK_SIZE} overlap={CHUNK_OVERLAP} top_k={TOP_K}\n")
    hits = 0

    for case in ANSWERABLE:
        results = retrieve(case["question"], chunks, vectors, TOP_K)
        rank = rank_of_expected(results, case["expect_source"])
        top_score = results[0][1] if results else 0.0

        if rank:
            hits += 1
            verdict, detail = OK, f"rank {rank}"
        else:
            verdict, detail = BAD, f"missing, top was {results[0][0]['source'][:34]}"

        print(
            f"  {verdict}  {case['id']:>2}  {case['question'][:52]:<52} "
            f"{_label(case['expect_source'])[:26]:<26} {detail:<40} {top_score:.3f}"
        )

    total = len(ANSWERABLE)
    print(f"\n  recall@{TOP_K}: {hits}/{total}  ({hits / total:.0%})")
    return hits, total


def run_cross_lingual(chunks, vectors):
    print("\nCROSS-LINGUAL  (non-English question, English-only corpus)\n")
    hits = 0

    for case in CROSS_LINGUAL:
        results = retrieve(case["question"], chunks, vectors, TOP_K)
        rank = rank_of_expected(results, case["expect_source"])

        if rank:
            hits += 1
            verdict, detail = OK, f"rank {rank}"
        else:
            verdict, detail = BAD, "missing"

        print(
            f"  {verdict}  {case['id']:<6} [{case['lang']}] "
            f"{case['question'][:50]:<50} -> EN q{case['mirrors']:<3} {detail}"
        )

    total = len(CROSS_LINGUAL)
    print(f"\n  cross-lingual recall@{TOP_K}: {hits}/{total}  ({hits / total:.0%})")
    return hits, total


def run_refusal(chunks, vectors):
    print("\nREFUSAL  (calls the model, costs a few cents)\n")
    refused = 0
    kinds: dict[str, int] = {}
    totals: dict[str, int] = {}

    for case in MUST_REFUSE:
        results = retrieve(case["question"], chunks, vectors, TOP_K)
        text = answer(case["question"], results).lower()
        did_refuse = any(marker in text for marker in REFUSAL_MARKERS)

        if did_refuse:
            refused += 1
            verdict, detail = OK, "refused"
        else:
            verdict, detail = BAD, "ANSWERED - should have refused"

        kinds[case["kind"]] = kinds.get(case["kind"], 0) + (1 if did_refuse else 0)
        totals[case["kind"]] = totals.get(case["kind"], 0) + 1

        print(
            f"  {verdict}  {case['id']:>2}  [{case['kind']:<5}] "
            f"{case['question'][:50]:<50} {detail}"
        )
        print(f"                    why: {case['why']}")

    total = len(MUST_REFUSE)
    print(f"\n  refusal rate: {refused}/{total}  ({refused / total:.0%})")
    for kind in sorted(totals):
        note = "fragile, valid only while the corpus is unchanged" if kind == "scope" else "permanent"
        print(f"    {kind:<5} {kinds.get(kind, 0)}/{totals[kind]}   {note}")
    return refused, total


def save_results(payload):
    STORAGE_DIR.mkdir(exist_ok=True)
    EVAL_RESULTS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main():
    with_generation = "--full" in sys.argv
    chunks, vectors = load_index()
    print(f"index: {len(chunks)} chunks")

    hits, total = run_retrieval(chunks, vectors)
    xl_hits, xl_total = run_cross_lingual(chunks, vectors)

    payload = {
        "measured_on": date.today().isoformat(),
        "chunks": len(chunks),
        "top_k": TOP_K,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "reranker": RERANK_MODEL if RERANK_ENABLED else None,
        "recall": f"{hits}/{total}",
        "cross_lingual": f"{xl_hits}/{xl_total}",
    }

    if with_generation:
        refused, refuse_total = run_refusal(chunks, vectors)
        payload["refusal"] = f"{refused}/{refuse_total}"
        save_results(payload)
        print(
            f"\nSUMMARY  recall {hits}/{total}  "
            f"cross-lingual {xl_hits}/{xl_total}  "
            f"refusal {refused}/{refuse_total}\n"
        )
    else:
        save_results(payload)
        print(
            f"\nSUMMARY  recall {hits}/{total}  cross-lingual {xl_hits}/{xl_total}"
            "   (--full also tests refusals)\n"
        )


if __name__ == "__main__":
    main()
