from pypdf import PdfReader
from pathlib import Path


def load_pdf(path) -> list[dict]:
    reader = PdfReader(path)
    filename = Path(path).name
    result = []

    for number, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        result.append({
            "source": filename,
            "page": number,
            "text": text,
        })

    return result

if __name__ == "__main__":
    pages = load_pdf("data/raw/i-140instr.pdf")
    print(f"страниц: {len(pages)}")
    print(pages[0]["text"][:500])
    print(pages[0])
    