"""End-to-end RAG: (history, question) -> answer + sources."""
import re
from functools import lru_cache

from .. import config
from . import llm, prompt_builder as pb, storage
from .embeddings import Embedder
from .retrieval import Index


@lru_cache(maxsize=1)
def _load():
    storage.ensure_assets()
    return Embedder(), Index(config.INDEX_DIR)


GENERIC_TITLES = {"", "FAST - NUCES Peshawar"}


def _source(c: dict) -> dict:
    # many scraped pages share the generic site title; fall back to the first heading
    title = c["title"] if c["title"] not in GENERIC_TITLES else (c["heading_path"].split(" > ")[0] or c["url"])
    return {"title": title, "heading": c["heading_path"], "url": c["url"], "page": c["page"], "score": round(c["score"], 3)}


def renumber(text: str, n_hits: int) -> tuple[str, list[int]]:
    """Map the model's [n] markers (indices into the hits) to 1..k in order of first use,
    so they match the returned sources list. Markers outside 1..n_hits are dropped."""
    order: list[int] = []

    def sub(m: re.Match) -> str:
        n = int(m.group(1))
        if not 1 <= n <= n_hits:
            return ""
        if n not in order:
            order.append(n)
        return f"[{order.index(n) + 1}]"

    return re.sub(r"\[(\d+)\]", sub, text), order


def answer(question: str, history: list[dict] | None = None) -> dict:
    history = history or []
    emb, index = _load()

    query = question
    if history:  # resolve follow-ups like "and the fee?" into a standalone query
        try:
            query = llm.generate(pb.REWRITE_SYSTEM, pb.rewrite_contents(history, question), max_tokens=80, temperature=0) or question
        except llm.LLMUnavailable:
            query = question

    hits = index.search(emb.embed_query(query), config.TOP_K)
    if hits[0]["score"] < config.MIN_SCORE:
        return {"answer": pb.NOT_FOUND_REPLY, "sources": [], "query": query, "found": False}

    text = llm.generate(pb.SYSTEM, pb.answer_contents(history, question, hits))
    if text.strip().startswith("NOT_FOUND"):
        return {"answer": pb.NOT_FOUND_REPLY, "sources": [], "query": query, "found": False}

    text, cited = renumber(text, len(hits))
    used = [hits[n - 1] for n in cited]  # uncited answer (e.g. "only Peshawar info") shows no sources
    return {"answer": text, "sources": [_source(c) for c in used], "query": query, "found": True}
