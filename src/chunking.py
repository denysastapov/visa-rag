def chunk_text(text, chunk_size=2000, overlap=200) -> list[str]:
    text_list = []

    for start in range(0, len(text), chunk_size - overlap):
        text_list.append(text[start : start + chunk_size])

    return text_list


def chunk_pages(pages, chunk_size=2000, overlap=200) -> list[dict]:
    result = []

    for page in pages:
        pieces = chunk_text(page["text"], chunk_size, overlap)
        for number, piece in enumerate(pieces, start=1):
            result.append(
                {
                    "source": page["source"],
                    "page": page["page"],
                    "chunk": number,
                    "text": piece,
                }
            )

    return result


if __name__ == "__main__":
    demo = "A" * 100 + "B" * 100 + "C" * 100
    chunks = chunk_text(demo, chunk_size=100, overlap=20)
    print("parts:", len(chunks))
    for c in chunks:
        print(len(c), c[:15], "...", c[-15:])
