from pathlib import Path

from pypdf import PdfReader


def load_pdf(path) -> list[dict]:
    reader = PdfReader(path)
    filename = Path(path).name
    result = []

    for number, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        result.append(
            {
                "source": filename,
                "page": number,
                "text": text,
            }
        )

    return result


def load_all_pdfs(folder) -> list[dict]:
    result = []

    for pdf_path in sorted(Path(folder).glob("*.pdf")):
        pages = load_pdf(pdf_path)
        result.extend(pages)

    return result


if __name__ == "__main__":
    pages = load_all_pdfs("data/raw")
    print(f"pages: {len(pages)}")
    print(pages[0]["source"], "|", pages[-1]["source"])
