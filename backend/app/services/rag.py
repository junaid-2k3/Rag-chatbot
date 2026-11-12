"""End-to-end RAG: (history, question) -> answer + sources."""
import re
from functools import lru_cache
from urllib.parse import unquote, urlparse

from .. import config
from . import llm, prompt_builder as pb, storage
from .embeddings import Embedder
from .retrieval import Index


@lru_cache(maxsize=1)
def _load():
    storage.ensure_assets()
    return Embedder(), Index(config.INDEX_DIR)


GENERIC_TITLES = {"", "FAST - NUCES Peshawar"}


def _pdf_title(url: str) -> str:
    name = unquote(urlparse(url).path.rsplit("/", 1)[-1])
    return re.sub(r"[_-]+", " ", re.sub(r"\.pdf$", "", name, flags=re.I)).strip() or url


def _source(c: dict) -> dict:
    # scraped PDFs have only a hash as title and many pages share the generic site title
    if c["source_type"] == "pdf":
        title = _pdf_title(c["url"])
    elif c["title"] in GENERIC_TITLES:
        title = c["heading_path"].split(" > ")[0] or c["url"]
    else:
        title = c["title"]
    return {"title": title, "heading": c["heading_path"], "url": c["url"], "page": c["page"], "score": round(c["score"], 3)}


def renumber(text: str, keys: list[str]) -> tuple[str, list[int]]:
    """Map the model's [n] markers (n = 1-based hit number) to one number per distinct source
    (keys[n-1], the hit's URL), in order of first use, so they match the deduplicated sources list.
    Markers outside 1..len(keys) are dropped. Returns the text and, per source, its first cited hit number."""
    first_hit: dict[str, int] = {}

    def sub(m: re.Match) -> str:
        n = int(m.group(1))
        if not 1 <= n <= len(keys):
            return ""
        first_hit.setdefault(keys[n - 1], n)
        return f"[{list(first_hit).index(keys[n - 1]) + 1}]"

    out = re.sub(r"\[(\d+)\]", sub, text)
    out = re.sub(r"(\[\d+\])(?:,?\s*\1)+", r"\1", out)  # "[1], [1]" -> "[1]"
    return out, list(first_hit.values())


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

    text, cited = renumber(text, [h["url"] for h in hits])
    used = [hits[n - 1] for n in cited]  # uncited answer (e.g. "only Peshawar info") shows no sources
    return {"answer": text, "sources": [_source(c) for c in used], "query": query, "found": True}
