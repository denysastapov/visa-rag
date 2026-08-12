import sys

from config import TOP_K
from src.embeddings import embed_query
from src.generate import answer
from src.index import load_index, search


def main() -> None:
    question = " ".join(sys.argv[1:]).strip() or input("Question: ").strip()
    if not question:
        return

    chunks, vectors = load_index()
    query_vector = embed_query(question)
    results = search(query_vector, chunks, vectors, TOP_K)

    print("\nRetrieved:")
    for chunk, score in results:
        print(f"  {score:.3f}  {chunk['source']} p.{chunk['page']}")

    print("\n" + answer(question, results) + "\n")


if __name__ == "__main__":
    main()
