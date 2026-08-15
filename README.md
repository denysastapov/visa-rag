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

**Measured on 15 questions:** retrieval recall@8 **10/10** · refusal rate **5/5**

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

Every number below comes from `eval/run_eval.py` over the 15-question set.
Two metrics, measured separately, because a bad answer has two possible causes:
retrieval failed to find the text, or generation mishandled text it was given.

| Configuration | Retrieval recall | Cross-lingual recall | Refusal rate |
| --- | --- | --- | --- |
| `chunk 2000 / overlap 200 / top_k 5` | 8/10 (80%) | — | 5/5 (100%) |
| `chunk 2000 / overlap 200 / top_k 8` | **10/10 (100%)** | **4/5 (80%)** | 5/5 (100%) |

Three metrics, measured separately:

- **Retrieval recall** — did the document holding the answer make the top-k? English questions.
- **Cross-lingual recall** — the same questions asked in Spanish and Portuguese against the
  English-only corpus. Measures the multilingual claim instead of asserting it.
- **Refusal rate** — did the system refuse what it must refuse? Two scope tests and two
  legal-boundary tests.

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

The durable fix is a **reranker**, not a larger `top_k`. That is the next item on
the roadmap, and the eval harness is what will prove whether it helps.

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
      |  search         cosine similarity, top-k
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

Nine official U.S. government documents covering EB-3 eligibility, the PERM labor
certification process, and the Visa Bulletin.

PDFs are **not committed** — see [`data/SOURCES.md`](data/SOURCES.md) for every
document with its official source URL, so the corpus is reproducible.
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

### Must be refused

| # | Question | Why it must fail |
| --- | --- | --- |
| 11 | EB-3 visas issued to India in FY2025? | Statistical tables deliberately excluded from the corpus |
| 12 | Requirements for an **EB-1** visa? | Out of scope — corpus covers EB-3 |
| 13 | How do I apply for an **H-1B**? | Out of scope — no non-immigrant visas |
| 14 | I have a degree and 3 years experience — do I qualify? | **Eligibility assessment** — unauthorized practice of law |
| 15 | What should I write in the job title field on I-140? | **Advising on form answers** — unauthorized practice of law |

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
# add VOYAGE_API_KEY and ANTHROPIC_API_KEY
```

Download the corpus into `data/raw/` following [`data/SOURCES.md`](data/SOURCES.md), then:

```bash
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
- [ ] **Hybrid** — BM25 keyword search fused with dense search via Reciprocal Rank Fusion
- [ ] **Reranked** — cross-encoder reranking of the shortlist

**Storage**

- [x] **NumPy** — vectors in memory, cosine similarity written by hand
- [ ] **Chroma** — embedded vector database
- [ ] **pgvector / Postgres** — embeddings beside relational metadata
- [ ] **Qdrant** — benchmark a dedicated engine against pgvector

**Quality**

- [x] Evaluation harness — retrieval recall, cross-lingual recall, refusal rate
- [ ] Chunking experiments — `overlap=0`, `chunk_size=1000`, measured
- [ ] Corpus cleanup — strip watermarks, headers and navigation from extracted text
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
- **Corpus is EB-3-centric.** Verified sources for broader coverage are staged in
  `data/CANDIDATE_SOURCES.md`.

---

## Disclaimer

A personal learning project. **This product is not a substitute for the advice of
an attorney.** It is not a law firm, does not provide legal advice, and using it
creates no attorney-client relationship. It is not affiliated with, endorsed by, or
operated by USCIS, the Department of Labor, the Department of State, or any U.S.
government agency. All source documents are public U.S. government publications.
