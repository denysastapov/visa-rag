def chunk_text(text, chunk_size=2000, overlap=200) -> list[str]:
    text_list = []

    for start in range(0, len(text), chunk_size - overlap):
        text_list.append(text[start : start + chunk_size])

    return text_list


if __name__ == "__main__":
    demo = "A" * 100 + "B" * 100 + "C" * 100
    chunks = chunk_text(demo, chunk_size=100, overlap=20)
    print("parts:", len(chunks))
    for c in chunks:
        print(len(c), c[:15], "...", c[-15:])
