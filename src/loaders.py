from pathlib import Path

from bs4 import BeautifulSoup
from pypdf import PdfReader

STRIP_TAGS = ["script", "style", "nav", "header", "footer", "noscript", "form", "svg"]
STRIP_SELECTORS = [
    ".usa-banner",
    ".usa-skipnav",
    ".breadcrumb",
    ".usa-breadcrumb",
    "#usa-footer",
    ".site-alert",
    ".skip-link",
]
HTML_PAGE_CHARS = 6000
DOCUMENT_SUFFIXES = {".pdf", ".html", ".htm"}


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


def load_html(path) -> list[dict]:
    filename = Path(path).name
    markup = Path(path).read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(markup, "html.parser")

    for tag in soup(STRIP_TAGS):
        tag.decompose()
    for selector in STRIP_SELECTORS:
        for tag in soup.select(selector):
            tag.decompose()

    body = soup.find("main") or soup.find("article") or soup.body or soup
    text = "\n".join(line.strip() for line in body.get_text("\n").splitlines() if line.strip())

    return [
        {
            "source": filename,
            "page": number,
            "text": text[start : start + HTML_PAGE_CHARS],
        }
        for number, start in enumerate(range(0, len(text), HTML_PAGE_CHARS), start=1)
    ]


def load_file(path) -> list[dict]:
    suffix = Path(path).suffix.lower()
    if suffix == ".pdf":
        return load_pdf(path)
    if suffix in {".html", ".htm"}:
        return load_html(path)
    return []


def load_all_pdfs(folder) -> list[dict]:
    result = []

    for path in sorted(Path(folder).glob("*")):
        if path.suffix.lower() in DOCUMENT_SUFFIXES:
            result.extend(load_file(path))

    return result


if __name__ == "__main__":
    pages = load_all_pdfs("data/raw")
    print(f"pages: {len(pages)}")
    print(pages[0]["source"], "|", pages[-1]["source"])
