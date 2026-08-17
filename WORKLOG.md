# Worklog

Where the project stands and what comes next. Written down because sessions are short.

---

## Running it

Local URL: **https://visa-rag.dev.test** (via the shared `~/dev-proxy` Traefik).

```bash
docker compose up -d                 # start (auto-restarts after reboot)
docker compose logs -f app           # follow logs
docker compose down                  # stop

docker compose run --rm index        # rebuild the index after corpus changes
docker compose run --rm eval         # run the evaluation harness
```

One-time setup on a fresh machine:

```bash
docker network create web                                  # if missing
docker compose -f ~/dev-proxy/docker-compose.yml up -d      # shared proxy
echo '127.0.0.1 visa-rag.dev.test' | sudo tee -a /etc/hosts
```

---

## What is built

| Piece | File | What it does |
| --- | --- | --- |
| PDF loading | `src/loaders.py` | Reads PDFs page by page, keeps source + page number |
| HTML loading | `src/loaders.py` | Same, for fetched government web pages |
| Corpus fetching | `fetch_corpus.py` | Downloads every source in `data/sources.json` with a browser User-Agent |
| Chunking | `src/chunking.py` | 2000 chars, 200 overlap, metadata carried onto each chunk |
| Embeddings | `src/embeddings.py` | Voyage `voyage-4`, batched and throttled, query cache on disk |
| Index + search | `src/index.py` | NumPy array, cosine similarity by hand |
| Reranking | `src/rerank.py` | Cross-encoder over the shortlist, max 3 chunks per source |
| Retrieval pipeline | `src/retrieval.py` | Ties dense search and reranking together |
| Generation | `src/generate.py` | Claude Haiku 4.5, grounding rules + 7 UPL refusal classes |
| CLI | `ask.py` | Question in, answer with citations out |
| Web UI | `app/streamlit_app.py` | Answer beside the retrieved chunks and their scores |
| Evaluation | `eval/run_eval.py` | Retrieval recall, cross-lingual recall, refusal rate |

---

## Measured baseline

`chunk_size=2000, overlap=200, top_k=8`, rerank 25 -> 8, 19 documents / 223 chunks

```
retrieval recall@8    14/14
cross-lingual          5/5     <- reranker took this from 3/5
refusal rate           6/6     (legal 3/3 permanent, scope 3/3 fragile)
```

Every expected document now lands in the top 5. Before the reranker several scraped in
at rank 7 or 8, which is a passing score built on luck.

Findings worth remembering:

1. **The Visa Bulletin swamps queries.** Dense tables carrying the vocabulary of a
   question but not its answer. It beat the correct source on two questions at `top_k=5`.
2. **The cross-lingual gap amplifies existing weakness.** The Spanish question that
   fails mirrors the English question that scraped in at rank 8 of 8. Fixing the weak
   English case should fix the Spanish one too.
3. **Growing the corpus 9 -> 19 dropped cross-lingual recall and English noticed nothing.**
   Without that second metric the regression would have shipped behind a green 100%.
4. **The eval set goes stale before the system does.** Three refusal tests broke after the
   expansion because the corpus had moved, not because the system misbehaved. Scope
   refusals are fragile; legal refusals are permanent.
5. **A broad overview page silently widens apparent scope.** The green-card-categories page
   lists fifteen paths one line each — enough for the model to say something about the
   diversity visa lottery without any real coverage of it.

---

## Next

**1. Hybrid retrieval (BM25 + dense, fused with Reciprocal Rank Fusion).** The one
remaining retrieval upgrade. Dense search still struggles with exact identifiers —
form numbers, INA section cites — which is exactly what keyword search is good at.

**2. Two travel.state.gov sources still missing.** Akamai refuses even a browser
User-Agent, so `what-is-a-us-visa` and `directory-of-visa-categories` need a manual
download or a headless browser. Everything else fetches with `python fetch_corpus.py`.

**3. Corpus cleanup.** Strip watermarks, page footers and site navigation from
extracted text. Measure the effect rather than assuming it helps.

**4. Visa Bulletin calculator.** "Which chart applies this month, and how far is my
priority date from the cut-off." Deterministic arithmetic over published State
Department data.

> **Architectural rule, non-negotiable:** the calculator never touches the language
> model, and the model never sees the user's dates. Computing a published figure is
> not legal advice; conditioning a generated answer on someone's personal facts is.
> Wiring the two together would collapse the refusal architecture.

Data notes for when that starts: the bulletin index lives at
`travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin.html`, the year in
the URL is the **fiscal** year (Oct–Dec 2025 sit under `/2026/`), there is no API,
the table schema drifts between months, and positional column indexing yields wrong
numbers rather than errors. Which chart applies each month is published as **prose**
on the USCIS filing-charts page — nobody parses it, and that is the actual gap.

---

## Decisions already made, so they are not relitigated

- **No vector database yet.** NumPy first, deliberately, to understand the mechanics.
  Chroma → pgvector → Qdrant are on the roadmap as a comparison exercise.
- **The corpus is never translated.** USCIS states the English version is the official
  one; citing a machine translation would be citing text with no legal force. Answer in
  the user's language, quote the English verbatim.
- **Form numbers and legal terms of art are never translated** — they must match what
  the applicant sees on paper.
- **Character-based chunking, not token-based.** A deliberate simplification, documented
  in the README under Known limitations.
- **Statistical tables stay out of the corpus.** They extract as noise and RAG handles
  numeric table lookup poorly. Eval question 11 tests that the system admits it.
- **Spanish is the target language**, not Russian — that is where the search-results gap
  actually is, and where AI-search visibility is highest.
