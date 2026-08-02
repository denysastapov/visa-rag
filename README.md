# visa-rag

A retrieval-augmented generation (RAG) system that answers questions about U.S.
**EB-3 employment-based immigration** using only official government sources —
and cites the exact document it took each answer from.

Built from scratch (no LangChain / LlamaIndex in the first version) to understand
every stage of the pipeline: chunking, embeddings, vector search, and grounded
generation.

> **Status:** 🚧 Phase 1 — document loading & chunking

---

## Why

Immigration rules live in dense PDFs and policy manuals. Answering "does my job
qualify as a Skilled Worker or an Other Worker?" means digging through the USCIS
Policy Manual, cross-referencing the DOL labor certification forms, and decoding
the monthly Visa Bulletin.

A general-purpose chatbot will confidently make this up. This system will not:
it answers **only** from a fixed corpus of official documents, and every answer
points back to its source. If the answer isn't in the corpus, it says so.

---

## Architecture

Two phases — indexing runs once, querying runs per question.

```
INDEXING (offline, run once)
  PDF documents
      |  load          (pypdf)
  raw text
      |  chunk         (~512 tokens, recursive splitter)
  text chunks + metadata (source file, page)
      |  embed         (Voyage voyage-4)
  vectors
      |  store
  vector index

QUERYING (online, per question)
  user question
      |  embed         (same model - this matters)
  query vector
      |  retrieve      (top-k nearest by cosine similarity)
  relevant chunks
      |  generate      (Claude Haiku 4.5, chunks injected into prompt)
  answer + citations
```

**Deliberate choice:** the first version uses **no vector database at all** —
vectors live in a NumPy array and nearest-neighbour search is plain cosine
similarity. A vector DB is added only in Phase 2, once the mechanics are
understood rather than assumed.

---

## Roadmap

Each step is measured against the evaluation set below, so improvements are
demonstrated rather than claimed.

**Retrieval quality**
- [ ] **Naive** — dense vector search only (baseline)
- [ ] **Hybrid** — BM25 keyword search fused with dense search (Reciprocal Rank Fusion)
- [ ] **Reranked** — cross-encoder reranking of the shortlist

**Storage**
- [ ] **NumPy** — vectors in memory, cosine similarity by hand (understand it)
- [ ] **Chroma** — embedded vector database (see that it does the same thing)
- [ ] **pgvector / Postgres** — production-realistic, embeddings beside relational metadata
- [ ] **Qdrant** — benchmark a dedicated vector engine against pgvector

**Interface**
- [ ] CLI
- [ ] Streamlit (surface retrieved chunks + scores, so retrieval is visible)

---

## Corpus

Nine official U.S. government documents covering EB-3 eligibility, the PERM
labor certification process, and the Visa Bulletin.

PDFs are **not committed** to this repository — see [`data/SOURCES.md`](data/SOURCES.md)
for every document, its official source URL, and how to reproduce the corpus.

Primary sources:
- USCIS Policy Manual **6-F-7** — Skilled Worker, Professional, or Other Worker
- USCIS Policy Manual **6-E-6** — Permanent Labor Certification
- Form **I-140** instructions (USCIS)
- Form **ETA-9089** general instructions (DOL)
- Visa Bulletin (June & July 2026) + USCIS priority-date guidance

---

## Evaluation set

> **REVIEW ME** — this is a starter set. Read the corpus, delete what doesn't
> matter, and add the questions that actually matter to you. These questions are
> the yardstick for every change to the pipeline.

The point of a fixed question set: when chunk size changes, or BM25 is added, or
a reranker is bolted on, the only honest way to say *"this made it better"* is to
measure against the same questions.

### Answerable from the corpus

| # | Question | Expected answer (key fact) | Source |
|---|----------|---------------------------|--------|
| 1 | What are the education and experience requirements for the EB-3 **Skilled Worker** category? | Job must require **at least 2 years** of training or experience; not temporary or seasonal | PM 6-F-7 |
| 2 | How does the **Professional** subcategory differ from **Skilled Worker**? | Professional requires a **U.S. bachelor's degree or foreign equivalent**; education and experience **cannot be substituted** for the degree | PM 6-F-7 |
| 3 | Who qualifies as an **Other Worker** (unskilled)? | Job requires **less than 2 years** of training or experience | PM 6-F-7 |
| 4 | How many EB-3 visas are available per fiscal year? | **40,000**, of which no more than **10,000** may go to "other" (unskilled) workers | PM 6-F-7 |
| 5 | What is **PERM** / labor certification, and **who files it** — the worker or the employer? | The **employer** files it with the **Department of Labor** (Form ETA-9089), before the I-140 | PM 6-E-6, ETA-9089 |
| 6 | Which form is the EB-3 immigrant petition, and who submits it? | **Form I-140**, filed by the **employer** with USCIS | I-140 instructions |
| 7 | What does **Final Action Date** mean in the Visa Bulletin? | The date at which a green card may actually be **issued / approved** | USCIS filing charts |
| 8 | What is the difference between **Final Action Dates** and **Dates for Filing**? | Dates for Filing = when the application may be **submitted**; Final Action = when it may be **approved** | USCIS filing charts |
| 9 | What is a **priority date** and how is it established? | Established by the filing of the labor certification (or the I-140, where no labor cert is required) | USCIS priority dates |
| 10 | Is EB-3 current for a worker born in India per the July 2026 bulletin? | (read the July 2026 chart) | Visa Bulletin July 2026 |

### Must NOT be answerable — the system has to say "I don't know"

These are the honesty tests. A system that answers them is hallucinating.

| # | Question | Why it must fail |
|---|----------|------------------|
| 11 | How many EB-3 visas were issued to India in FY2025? | Statistical tables are deliberately not in the corpus |
| 12 | What are the requirements for an **EB-1** visa? | Out of scope — the corpus covers EB-3 only |
| 13 | How do I apply for an **H-1B**? | Out of scope — non-immigrant visas are not in the corpus |

---

## Setup

Requires Python 3.12+.

```bash
git clone https://github.com/denysastapov/visa-rag.git
cd visa-rag

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# add your VOYAGE_API_KEY and ANTHROPIC_API_KEY
```

Then download the corpus into `data/raw/` following [`data/SOURCES.md`](data/SOURCES.md).

> Note: `uscis.gov` and `dol.gov` return **HTTP 403** to non-browser user agents.
> Download through a browser, or set a browser `User-Agent` header if scripting.

---

## Tech stack

| Concern | Choice | Why |
|---------|--------|-----|
| PDF parsing | `pypdf` | Simple, no system dependencies |
| Embeddings | Voyage `voyage-4` | Anthropic-recommended; 200M free tokens; tops retrieval benchmarks |
| Generation | Claude Haiku 4.5 | Fractions of a cent per answer; strong at staying grounded |
| Vector search | NumPy → Chroma → pgvector | Understand it, then use a DB, then make it production-realistic |

The embedding client and the chat client sit behind a thin interface, so the whole
pipeline can be swapped to fully local models (Ollama + `nomic-embed-text`) and run
offline at zero cost.

---

## Disclaimer

A personal learning project. **Not legal advice**, and not affiliated with USCIS,
the Department of Labor, or the Department of State. All source documents are
public U.S. government publications.
