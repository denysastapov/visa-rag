from config import CHUNK_OVERLAP, CHUNK_SIZE, DATA_DIR
from src.chunking import chunk_pages
from src.embeddings import embed_documents
from src.index import save_index
from src.loaders import load_all_pdfs


def main() -> None:
    print("1/4 loading PDFs")
    pages = load_all_pdfs(DATA_DIR)
    print(f"      {len(pages)} pages")

    print(f"2/4 chunking (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    chunks = chunk_pages(pages, CHUNK_SIZE, CHUNK_OVERLAP)
    print(f"      {len(chunks)} chunks")

    print("3/4 embedding via Voyage")
    vectors = embed_documents([c["text"] for c in chunks])

    print("4/4 saving index")
    save_index(chunks, vectors)
    print("done")


if __name__ == "__main__":
    main()
