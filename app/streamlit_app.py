import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from config import CHAT_MODEL, CHUNK_OVERLAP, CHUNK_SIZE, EMBEDDING_MODEL, TOP_K
from src.embeddings import embed_query
from src.generate import answer
from src.index import load_index, search

EXAMPLES = [
    ("EN", "How many EB-3 visas are available each fiscal year?"),
    ("EN", "Who files the PERM labor certification, the worker or the employer?"),
    ("ES", "¿Qué significa la Fecha de Acción Final en el Boletín de Visas?"),
    ("ES", "¿Quién presenta la certificación laboral PERM?"),
    ("REFUSE", "I have a bachelor degree and 3 years of experience. Do I qualify for EB-3?"),
    ("REFUSE", "How do I apply for an H-1B visa?"),
]

st.set_page_config(page_title="visa-rag", page_icon="📄", layout="wide")


@st.cache_resource
def get_index():
    return load_index()


def render_sources(results):
    for chunk, score in results:
        label = f"{score:.3f} · {chunk['source'][:58]} · p. {chunk['page']}"
        with st.expander(label):
            st.text(chunk["text"])


def main():
    chunks, vectors = get_index()

    with st.sidebar:
        st.subheader("Corpus")
        sources = sorted({c["source"] for c in chunks})
        st.metric("documents", len(sources))
        st.metric("chunks indexed", len(chunks))

        st.subheader("Configuration")
        st.code(
            f"chunk_size   {CHUNK_SIZE}\n"
            f"overlap      {CHUNK_OVERLAP}\n"
            f"top_k        {TOP_K}\n"
            f"embeddings   {EMBEDDING_MODEL}\n"
            f"generation   {CHAT_MODEL}",
            language=None,
        )

        st.subheader("Measured quality")
        st.code(
            "retrieval recall@8   10/10\n"
            "cross-lingual        4/5\n"
            "refusal rate         5/5",
            language=None,
        )
        st.caption("`python -m eval.run_eval --full`")

        with st.expander("Documents in corpus"):
            for name in sources:
                st.caption(name)

    st.title("visa-rag")
    st.caption(
        "Answers about US employment-based immigration from official government "
        "documents only — with the source page for every fact, in the language you ask."
    )

    st.info(
        "**This product is not a substitute for the advice of an attorney.** "
        "Not a law firm, not legal advice, no attorney-client relationship. "
        "Not affiliated with USCIS, the Department of Labor, or the Department of State."
    )

    if "question" not in st.session_state:
        st.session_state.question = ""

    st.write("Try one:")
    columns = st.columns(3)
    for position, (tag, text) in enumerate(EXAMPLES):
        with columns[position % 3]:
            if st.button(f"{tag} · {text[:38]}…", key=f"ex{position}", use_container_width=True):
                st.session_state.question = text

    question = st.text_input(
        "Question",
        value=st.session_state.question,
        placeholder="Ask in any language — the corpus is English only",
    )

    if not question:
        return

    with st.spinner("Searching the corpus"):
        results = search(embed_query(question), chunks, vectors, TOP_K)

    left, right = st.columns([3, 2])

    with right:
        st.subheader("Retrieved")
        st.caption("Cosine similarity against every chunk. Higher is closer in meaning.")
        render_sources(results)

    with left:
        st.subheader("Answer")
        with st.spinner("Reading the sources"):
            st.markdown(answer(question, results))


if __name__ == "__main__":
    main()
