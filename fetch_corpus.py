import json
import sys
import time
import urllib.error
import urllib.request

from config import DATA_DIR, SOURCES_PATH

BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

HEADERS = {
    "User-Agent": BROWSER_UA,
    "Accept": "text/html,application/xhtml+xml,application/pdf,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

DELAY = 2


def fetch(url: str, timeout: int = 45) -> bytes:
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def main() -> None:
    force = "--force" in sys.argv
    sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    fetched = skipped = failed = 0

    for source in sources:
        target = DATA_DIR / source["file"]

        if target.exists() and not force:
            print(f"  skip    {source['file']}")
            skipped += 1
            continue

        try:
            body = fetch(source["url"])
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as error:
            print(f"  FAILED  {source['file']}  {error}")
            failed += 1
            continue

        target.write_bytes(body)
        print(f"  ok      {source['file']}  {len(body) // 1024} KB")
        fetched += 1
        time.sleep(DELAY)

    print(f"\nfetched {fetched}, skipped {skipped}, failed {failed}")
    if fetched:
        print("run build_index.py to reindex")


if __name__ == "__main__":
    main()
