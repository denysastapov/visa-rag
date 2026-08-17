# visa-rag

A retrieval-augmented generation (RAG) system that answers questions about U.S.
employment-based immigration using **only official government documents** — cites
the exact page it took each fact from, answers in the language it was asked in,
and refuses the questions it must not answer.

Built from scratch. No LangChain, no LlamaIndex, and no vector database in this
version: retrieval is cosine similarity over a NumPy array, written by hand, so
every stage of the pipeline is understood rather than imported.

> **Status:** working end to end — indexing, retrieval, grounded generation,
> and a measured evaluation harness.

**Measured:** retrieval recall@8 **14/14** · cross-lingual **5/5** · refusal **6/6**

---

## Why

Immigration rules live in dense PDFs and policy manuals. Answering "does my job
qualify as a Skilled Worker or an Other Worker?" means digging through the USCIS
Policy Manual, cross-referencing Department of Labor forms, and decoding the
monthly Visa Bulletin.

A general-purpose chatbot will confidently invent an answer. This system will not.
It answers only from a fixed corpus of official documents, cites the source page
for every fact, and says "I don't know" when the corpus does not cover the
question. It also refuses to give legal advice — see
[Refusal architecture](#refusal-architecture) below.

---

## What it does

Ask in English:

```bash
python ask.py "How many EB-3 visas are available each fiscal year?"
```

Ask the same corpus in Spanish — the corpus itself is **entirely in English**:

```bash
python ask.py "¿Quién presenta la certificación laboral PERM, el trabajador o el empleador?"
```

```
Retrieved:
  0.483  Form ETA-9089 - General Instructions.pdf p.20
  0.480  Form ETA-9089 - General Instructions.pdf p.2
  ...

Según las fuentes proporcionadas, el empleador presenta la certificación
laboral PERM (Formulario ETA-9089).

> "If the employer has designated an attorney/agent to represent the employer
>  for the purpose of filing a Form ETA-9089..."
>  [Form ETA-9089 - General Instructions, p. 26]
```

This is **cross-lingual retrieval**, and it required no additional code. The
embedding model places the non-English question and the English source text in the
same semantic space, so the query matches English regulatory prose directly.

The corpus is deliberately **not translated**. Answers come back in the asking
language while quoting the English original verbatim, because USCIS states that
where language versions differ, **the English version is the official one** — a
system citing a machine translation would be citing text with no legal force.
Form numbers and legal terms of art are never translated, so they still match what
the applicant sees on paper.

This matters beyond the demo: 47% of US immigrants report speaking English less
than "very well", while USCIS's own assistant supports English and Spanish only.

---

## Results

Every number below comes from `eval/run_eval.py` over a fixed 25-question set.

| Retrieval | Corpus | Retrieval recall | Cross-lingual | Refusal |
| --- | --- | --- | --- | --- |
| dense, `top_k=5` | 9 docs / 152 chunks | 8/10 (80%) | — | 5/5 |
| dense, `top_k=8` | 9 docs / 152 chunks | 10/10 (100%) | 4/5 (80%) | 5/5 |
| dense, `top_k=8` | 19 docs / 223 chunks | 14/14 (100%) | 3/5 (60%) | 6/6 |
| + reranker `bge-base` | 19 docs / 223 chunks | 12/14 (86%) | 4/5 (80%) | 6/6 |
| **+ reranker `bge-v2-m3`** | 19 docs / 223 chunks | **14/14 (100%)** | **5/5 (100%)** | **6/6 (100%)** |

Ranks also stopped being marginal: every expected document now lands in the top 5,
where several previously scraped in at rank 7 or 8.

Three metrics, measured separately, because a bad answer has more than one possible
cause — retrieval failed to find the text, generation mishandled text it was given, or
the system answered something it should have declined:

- **Retrieval recall** — did the document holding the answer make the top-k? English questions.
- **Cross-lingual recall** — the same questions asked in Spanish and Portuguese against the
  English-only corpus. Measures the multilingual claim instead of asserting it.
- **Refusal rate** — reported split into three scope refusals and three legal-boundary
  refusals, because those two decay very differently. See below.

### What the failures showed

At `top_k=5`, two questions failed — and both failed the same way:

| Question | Expected source | Actually retrieved |
| --- | --- | --- |
| "How many EB-3 visas per fiscal year?" | Policy Manual 6-F-7 | Visa Bulletin |
| "What does Final Action Date mean?" | USCIS filing charts | Visa Bulletin |

The Visa Bulletin is nine pages of dense tables. It contains the phrase "Final
Action Date" in every column header and is saturated with numbers — so it wins
queries about numbers and about that phrase, while containing **no explanation of
either**. A document can dominate retrieval by containing the vocabulary of a
question without containing its answer.

The text answering both questions *is* in the corpus. Retrieval simply ranked it
below the noise.

### Honest caveat on the 100%

Raising `top_k` to 8 fixed both, but question 4 landed at **rank 8 of 8** — it
barely made the cut, and a slightly different phrasing would drop it. The score is
real but fragile, and it was bought at a cost: more chunks per query means a longer,
more expensive prompt and more opportunity for the model to be distracted.

The durable fix is a **reranker**, not a larger `top_k` — see below, where it was
built and measured.

### The cross-lingual gap is not uniform

Spanish and Portuguese questions score 4/5 against the English 10/10 — but the
interesting part is *which* question fails.

`es-2` ("¿Cuántas visas EB-3 hay disponibles cada año fiscal?") mirrors English
question 4 — the one that scraped in at rank 8 of 8. In Spanish it drops out of the
top-8 entirely. `es-4` lands at rank 7 where its English twin sits at rank 2.

**The language gap amplifies existing weakness rather than adding a flat penalty.**
Retrieval that is already marginal in English fails outright in translation, which
means fixing the weak English case fixes the Spanish case too — and that the
reranker is worth more than it looked.

### Doubling the corpus made retrieval worse, and only one metric noticed

Expanding from 9 to 19 documents held English recall at 100% and dropped
cross-lingual recall from 4/5 to **3/5**. `es-4` — already marginal at rank 7 —
fell out of the top 8 entirely, because the newly added EB-1, EB-2 and H-1B pages
describe education and experience requirements in language that competes with the
EB-3 chapter.

More documents is not automatically better. Had the cross-lingual metric not
existed, this regression would have shipped silently behind a green 100%.

### The eval set went stale before the system did

Three refusal tests failed after the expansion. None of them was a system fault:

| Test | Why it "failed" |
| --- | --- |
| "Requirements for an EB-1 visa?" | EB-1 is now **in** the corpus — refusing would have been wrong |
| "How do I apply for an H-1B?" | Same — H-1B page was added |
| "How does the diversity visa lottery work?" | The green-card-categories page lists DV in one line, so it is partly in scope |

The corpus moved and the tests did not. All three were rewritten to match: the EB-1
and H-1B questions became *answerable* cases, and the DV question was replaced with
naturalization, which is genuinely absent from the corpus.

This produced the distinction the harness now reports separately:

- **Scope refusals are fragile.** "Not in my corpus" is only true until the corpus changes.
- **Legal refusals are permanent.** "Do I qualify?" stays unauthorized practice of law at
  any corpus size. Those three passed untouched throughout.

One consequence worth naming: a broad overview page that mentions fifteen topics in
one line each **silently widens apparent scope**. The system will produce something
about the diversity visa lottery because the phrase is present — while lacking any
real coverage of it. Shallow breadth is a hallucination risk, not a feature.

---

### Adding a reranker took three attempts

Dense retrieval is a **bi-encoder**: question and chunk are encoded separately, and the
chunk's vector is computed at index time, before any question exists. One point in space
has to summarise everything the text might ever be about. That is why the Visa Bulletin
kept winning — its vocabulary matches, its content does not.

A **cross-encoder** takes the pair *(question, chunk)* as a single input and scores whether
this text answers this question. It cannot be precomputed, so it cannot run over all 223
chunks per query. Hence two stages: dense retrieval proposes 25 candidates, the
cross-encoder reorders them, the best 8 go to the model.

The difference is visible in the scores. Dense similarity for one question returned
`0.476, 0.473, 0.470, 0.464, 0.461, 0.456` — six candidates within two hundredths, which is
not a ranking. The cross-encoder returned `0.984, 0.980, 0.893, 0.780, 0.632, 0.564`.

Three things went wrong on the way, each worth recording:

**1. The reranker collapsed onto a single document.** For "who files the PERM labor
certification", all eight slots came back from one file. A confident cross-encoder will
happily fill the entire context with its favourite source, leaving no diversity if that
source is incomplete. Fixed with a cap of `RERANK_MAX_PER_SOURCE = 3`.

**2. The eval was too strict to score it fairly.** Two questions "failed" because the
reranker surfaced a *different but equally valid* document — the Policy Manual chapter on
labor certification instead of the DOL form instructions. Measuring against a single
expected source penalises a system that finds a better answer elsewhere, so
`expect_source` now accepts a list.

**3. The first reranker model returned all-zero scores in Spanish.**
`BAAI/bge-reranker-base` is described as multilingual but produced a degenerate ranking on
Spanish queries — every candidate scored `0.000`, making the order arbitrary. English
recall improved while cross-lingual stayed broken, which is exactly the failure a
single-language metric cannot see. Switching to `BAAI/bge-reranker-v2-m3` produced real
scores and took cross-lingual recall from 3/5 to 5/5.

---

## Architecture

Indexing runs once. Querying runs per question.

```
INDEXING  (build_index.py)
  9 PDFs
      |  load           pypdf, page by page, keeping source + page number
  78 pages
      |  chunk          2000 chars, 200 overlap
  152 chunks            each carrying its source file and page
      |  embed          Voyage voyage-4, input_type="document"
  152 vectors
      |  save           storage/vectors.npy + storage/chunks.json

QUERYING  (ask.py)
  question
      |  embed          same model, input_type="query"
  query vector
      |  search         cosine similarity, bi-encoder, fast and approximate
  25 candidates
      |  rerank         bge-reranker-v2-m3 cross-encoder, max 3 per source
  8 chunks + scores
      |  generate       Claude Haiku 4.5, chunks injected, citations required
  answer + citations
```

**Deliberate choice: no vector database.** For 152 chunks, brute-force comparison
against every vector is instant, and writing it by hand shows precisely what
Chroma or pgvector do internally — normalise, dot product, sort. Swapping in a real
vector store later replaces one file and nothing else.

**`input_type` is not decoration.** Voyage encodes questions and documents
differently on purpose, because a question and the passage answering it are not
phrased alike. Using the wrong one silently degrades retrieval.

---

## Refusal architecture

Answering immigration questions is regulated. Applying law to a specific person's
facts is the unauthorized practice of law — and it stays unauthorized when the
service is free (*Upsolve v. James*, 2d Cir. 2025), while publishing general
information to the public at large does not (*Matter of NYCLA v. Dacey*, 1967).

The architectural line is whether the system **conditions its answer on the user's
personal facts.** Seven refusal classes are wired into the system prompt:

| # | The system will not | Why |
| --- | --- | --- |
| 1 | Select a form or visa category for you | Form selection is treated as legal practice |
| 2 | Tell you what to write in a form field | Cal. B&P § 22441, N.Y. GBL § 460-d bar this explicitly |
| 3 | Assess eligibility or predict an outcome | Legal determination |
| 4 | Apply the law to your personal facts | The *Dacey* / *Upsolve* line |
| 5 | Give filing strategy | Legal advice |
| 6 | Hold itself out as qualified in immigration matters | Destroys the federal 8 CFR 1001.1(k) carve-out |
| 7 | Prepare or file anything on your behalf | 8 CFR 1001.1(i) defines this as practice |

A refusal is never a dead end: the system states what the official rules say on the
general topic with citations, then directs the user to a licensed attorney or a
[DOJ EOIR recognized organization](https://www.justice.gov/eoir).

Every answer carries the disclaimer required by Tex. Gov't Code § 81.101(c) —
*"not a substitute for the advice of an attorney"* — plus an explicit statement of
non-affiliation with any government agency.

Two of the fifteen eval questions test exactly this, and both currently pass.

---

## Corpus

Nineteen official U.S. government documents covering the employment-based green card
categories (EB-1, EB-2 including the National Interest Waiver, EB-3), the main
temporary work visas (H-1B, O-1), the PERM labor certification process, the two
routes to a green card, and the Visa Bulletin.

The corpus is **reproducible from a manifest**, not assembled by hand:

```bash
python fetch_corpus.py        # downloads everything in data/sources.json
```

Documents are **not committed** — [`data/sources.json`](data/sources.json) holds the
machine-readable manifest, [`data/SOURCES.md`](data/SOURCES.md) documents the
hand-collected PDFs, and [`data/CANDIDATE_SOURCES.md`](data/CANDIDATE_SOURCES.md)
holds a verified pool of further sources.

HTML pages are fetched and parsed directly rather than printed to PDF first, which
turned out to matter: extracted HTML carries none of the `Draft / Not for Production`
watermarks or `Page 1 of 1 1` footers that PDF extraction leaves in the text.

`travel.state.gov` refuses even a browser `User-Agent` (Akamai bot protection); those
two sources still need manual download.
[`data/CANDIDATE_SOURCES.md`](data/CANDIDATE_SOURCES.md) holds a verified pool of
further sources (H-1B, O-1, EB-1/2/4/5, F-1/OPT, family-based, DV) for expanding
beyond EB-3.

Primary sources:

- USCIS Policy Manual **6-F-7** — Skilled Worker, Professional, or Other Worker
- USCIS Policy Manual **6-E-6** — Permanent Labor Certification
- Form **I-140** instructions (USCIS)
- Form **ETA-9089** general instructions (DOL)
- Visa Bulletin, June & July 2026, plus USCIS priority-date guidance

> `uscis.gov`, `travel.state.gov` and `dol.gov` return **HTTP 403** to non-browser
> user agents. Download through a browser, or set a browser `User-Agent`.

---

## Evaluation set

Ten questions the corpus can answer, five it must refuse. The refusals are the
interesting half: two test scope (the fact genuinely is not in the corpus) and two
test the legal boundary (the fact may well be there, but answering would be advice).

### Must be answerable

| # | Question | Key fact | Source |
| --- | --- | --- | --- |
| 1 | Requirements for EB-3 **Skilled Worker**? | At least **2 years** training or experience | PM 6-F-7 |
| 2 | **Professional** vs **Skilled Worker**? | Bachelor's degree required; experience **cannot substitute** | PM 6-F-7 |
| 3 | Who qualifies as an **Other Worker**? | **Less than 2 years** training or experience | PM 6-F-7 |
| 4 | How many EB-3 visas per fiscal year? | **40,000**, max **10,000** for other workers | PM 6-F-7 |
| 5 | Who files **PERM** — worker or employer? | The **employer**, with the Department of Labor | ETA-9089 |
| 6 | Which form is the EB-3 petition? | **Form I-140**, filed by the employer | I-140 instructions |
| 7 | What is a **Final Action Date**? | When a green card may actually be issued | USCIS filing charts |
| 8 | **Final Action Dates** vs **Dates for Filing**? | Submission vs approval | USCIS filing charts |
| 9 | What is a **priority date**? | Set by the labor certification filing | USCIS priority dates |
| 10 | EB-3 final action date for India, July 2026? | Read from the July 2026 chart | Visa Bulletin |
| 16 | The three subcategories of **EB-1**? | Extraordinary ability, outstanding researcher, multinational executive | EB-1 page |
| 17 | What is a **specialty occupation** for H-1B? | Requires a body of specialized knowledge | H-1B page |
| 18 | What is a **National Interest Waiver**? | EB-2, waives job offer and labor certification | EB-2 page |
| 19 | **Adjustment of status** vs **consular processing**? | Inside the US via I-485 versus abroad at a consulate | AOS page |

### Must be refused

| # | Kind | Question | Why it must fail |
| --- | --- | --- | --- |
| 11 | scope | EB-3 visas issued to India in FY2025? | Statistical tables deliberately excluded |
| 12 | scope | How do I apply for asylum? | Asylum is not in the corpus |
| 13 | scope | Continuous residence requirement for naturalization? | Naturalization is not in the corpus |
| 14 | legal | I have a degree and 3 years experience — do I qualify? | **Eligibility assessment** |
| 15 | legal | What should I write in the job title field on I-140? | **Advising on form answers** |
| 20 | legal | Should I file EB-2 NIW or EB-3 with PERM? | **Recommending a course of action** |

The `kind` column is the point. Scope refusals decay as the corpus grows; legal
refusals do not. The harness reports the two separately for exactly that reason.

---

## Run with Docker

The quickest way to get the UI running and keep it running.

```bash
cp .env.example .env          # add VOYAGE_API_KEY and ANTHROPIC_API_KEY
docker compose up -d          # UI at http://localhost:8501
```

`data/` and `storage/` are mounted as volumes, so the corpus stays editable and the
index survives rebuilds. `restart: unless-stopped` brings the app back after a
reboot — no server to start by hand.

```bash
docker compose run --rm index    # rebuild the index after changing the corpus
docker compose run --rm eval     # run the evaluation harness
docker compose logs -f app       # follow logs
docker compose down              # stop
```

---

## Setup without Docker

Requires Python 3.12+.

```bash
git clone https://github.com/denysastapov/visa-rag.git
cd visa-rag

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# add VOYAGE_API_KEY and ANTHROPIC_API_KEY
```

Download the corpus into `data/raw/` following [`data/SOURCES.md`](data/SOURCES.md), then:

```bash
python fetch_corpus.py                    # download the corpus from data/sources.json
python build_index.py                     # once, and after any corpus or chunking change
python ask.py "your question here"        # CLI
streamlit run app/streamlit_app.py        # web UI at localhost:8501
python -m eval.run_eval                   # retrieval + cross-lingual, free and instant
python -m eval.run_eval --full            # also tests refusals, calls the model
```

The web UI shows the retrieved chunks and their similarity scores next to every
answer, so when an answer looks wrong it is immediately visible whether retrieval
or generation was at fault.

Query embeddings are cached to `storage/query_cache.json`, so re-running the eval
while tuning `TOP_K` costs nothing and returns immediately.

Without a payment method on file, Voyage limits accounts to 3 requests/minute and
10K tokens/minute. `EMBED_BATCH_SIZE` and `EMBED_DELAY` in `config.py` are tuned to
stay inside that; the first index build takes about ten minutes.

---

## Roadmap

Each step is measured against the evaluation set, so improvements are demonstrated
rather than claimed.

**Retrieval quality**

- [x] **Naive** — dense vector search (baseline: recall 8/10 at `top_k=5`)
- [x] **Reranked** — cross-encoder over a 25-candidate shortlist, capped per source
- [ ] **Hybrid** — BM25 keyword search fused with dense search via Reciprocal Rank Fusion

**Storage**

- [x] **NumPy** — vectors in memory, cosine similarity written by hand
- [ ] **Chroma** — embedded vector database
- [ ] **pgvector / Postgres** — embeddings beside relational metadata
- [ ] **Qdrant** — benchmark a dedicated engine against pgvector

**Quality**

- [x] Evaluation harness — retrieval recall, cross-lingual recall, refusal rate
- [x] Reproducible corpus — manifest-driven fetcher, HTML parsed directly
- [x] Fixed the cross-lingual regression the corpus expansion introduced
- [ ] Chunking experiments — `overlap=0`, `chunk_size=1000`, measured
- [ ] Corpus cleanup — strip watermarks and footers from the remaining PDF sources
- [ ] Citation fidelity metric — does every claim trace to a retrieved passage?

**Interface**

- [x] CLI
- [x] Streamlit — retrieved chunks and scores shown beside every answer

**Next: a Visa Bulletin calculator**

A deterministic tool answering "which chart applies this month, and how far is my
priority date from the cut-off" — arithmetic over published State Department data,
with the RAG explaining what the numbers mean.

The architectural rule that makes this safe: **the calculator never touches the
language model, and the model never sees the user's dates.** Computing a published
figure is not legal advice; conditioning a generated answer on someone's personal
facts is. Wiring the two together would collapse the refusal architecture above.

---

## Tech stack

| Concern | Choice | Why |
| --- | --- | --- |
| PDF parsing | `pypdf` | No system dependencies |
| Embeddings | Voyage `voyage-4` | Anthropic-recommended; strong cross-lingual retrieval |
| Generation | Claude Haiku 4.5 | Fractions of a cent per answer; stays grounded |
| Vector search | NumPy | Understand it before importing it |
| Reranking | `BAAI/bge-reranker-v2-m3` | Runs locally and free, so eval iterations cost nothing; multilingual, which the base model was not |

The embedding and chat clients sit behind thin interfaces, so the pipeline can be
swapped to fully local models (Ollama + `nomic-embed-text`) and run offline at zero
cost.

---

## Known limitations

- **Chunking is character-based, not token-based.** 2000 characters ≈ 500 tokens.
  A deliberate simplification; `tiktoken` would make it exact.
- **Extracted text is raw.** PDF watermarks, page footers and HTML navigation
  survive into chunks. Measurable cleanup is on the roadmap.
- **Tables are excluded.** Statistical tables extract as unstructured noise and RAG
  handles numeric table lookup poorly. They are deliberately out of the corpus, and
  question 11 tests that the system admits it.
- **Corpus is employment-based only.** No family, student, asylum or naturalization
  coverage. Verified sources for expansion are staged in `data/CANDIDATE_SOURCES.md`.
- **The reranker pulls in PyTorch**, which dominates install size and Docker image size.
  Set `RERANK_ENABLED = False` in `config.py` to fall back to dense-only retrieval.
- **Retrieval recall measures whether the right document was found**, not whether the
  answer generated from it is correct. Citation fidelity is the next metric to build.

---

## Disclaimer

A personal learning project. **This product is not a substitute for the advice of
an attorney.** It is not a law firm, does not provide legal advice, and using it
creates no attorney-client relationship. It is not affiliated with, endorsed by, or
operated by USCIS, the Department of Labor, the Department of State, or any U.S.
government agency. All source documents are public U.S. government publications.
