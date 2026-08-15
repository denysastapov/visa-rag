import sys

from config import CHUNK_OVERLAP, CHUNK_SIZE, TOP_K
from eval.questions import ANSWERABLE, CROSS_LINGUAL, MUST_REFUSE, REFUSAL_MARKERS
from src.embeddings import embed_query
from src.generate import answer
from src.index import load_index, search

OK = "PASS"
BAD = "FAIL"


def rank_of_expected(results, expect_source):
    for position, (chunk, _score) in enumerate(results, start=1):
        if expect_source.lower() in chunk["source"].lower():
            return position
    return None


def run_retrieval(chunks, vectors):
    print(f"\nRETRIEVAL  chunk_size={CHUNK_SIZE} overlap={CHUNK_OVERLAP} top_k={TOP_K}\n")
    hits = 0

    for case in ANSWERABLE:
        results = search(embed_query(case["question"]), chunks, vectors, TOP_K)
        rank = rank_of_expected(results, case["expect_source"])
        top_score = results[0][1] if results else 0.0

        if rank:
            hits += 1
            verdict, detail = OK, f"rank {rank}"
        else:
            verdict, detail = BAD, f"missing, top was {results[0][0]['source'][:34]}"

        print(
            f"  {verdict}  {case['id']:>2}  {case['question'][:52]:<52} "
            f"{case['expect_source'][:26]:<26} {detail:<40} {top_score:.3f}"
        )

    total = len(ANSWERABLE)
    print(f"\n  recall@{TOP_K}: {hits}/{total}  ({hits / total:.0%})")
    return hits, total


def run_cross_lingual(chunks, vectors):
    print("\nCROSS-LINGUAL  (non-English question, English-only corpus)\n")
    hits = 0

    for case in CROSS_LINGUAL:
        results = search(embed_query(case["question"]), chunks, vectors, TOP_K)
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

    for case in MUST_REFUSE:
        results = search(embed_query(case["question"]), chunks, vectors, TOP_K)
        text = answer(case["question"], results).lower()
        did_refuse = any(marker in text for marker in REFUSAL_MARKERS)

        if did_refuse:
            refused += 1
            verdict, detail = OK, "refused"
        else:
            verdict, detail = BAD, "ANSWERED - should have refused"

        print(f"  {verdict}  {case['id']:>2}  {case['question'][:52]:<52} {detail}")
        print(f"           why: {case['why']}")

    total = len(MUST_REFUSE)
    print(f"\n  refusal rate: {refused}/{total}  ({refused / total:.0%})")
    return refused, total


def main():
    with_generation = "--full" in sys.argv
    chunks, vectors = load_index()
    print(f"index: {len(chunks)} chunks")

    hits, total = run_retrieval(chunks, vectors)
    xl_hits, xl_total = run_cross_lingual(chunks, vectors)

    if with_generation:
        refused, refuse_total = run_refusal(chunks, vectors)
        print(
            f"\nSUMMARY  recall {hits}/{total}  "
            f"cross-lingual {xl_hits}/{xl_total}  "
            f"refusal {refused}/{refuse_total}\n"
        )
    else:
        print(
            f"\nSUMMARY  recall {hits}/{total}  cross-lingual {xl_hits}/{xl_total}"
            "   (--full also tests refusals)\n"
        )


if __name__ == "__main__":
    main()
