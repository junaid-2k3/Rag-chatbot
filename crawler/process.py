"""Turn data/raw + data/index.jsonl into data/markdown/*.md and data/chunks.jsonl."""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import pymupdf
from markdownify import markdownify as md
from scrapling.parser import Selector

ROOT = Path(__file__).resolve().parent.parent
RAW, MD = ROOT / "data" / "raw", ROOT / "data" / "markdown"
CHUNK_WORDS, OVERLAP_WORDS = 450, 60  # ~600 tokens, ~80 token overlap

CATEGORY_RULES = [
    (r"^/(faculty-profile|cs-faculty|ee-faculty|ce-faculty|hec-faculty|computer-science|electrical-engineering)", "faculty"),
    (r"^/(staff|staff-profile)", "staff"),
    (r"^/(society-profile|societies)", "societies"),
    (r"^/(upcoming-event-detail|news-detail|news|events)", "news_events"),
    (r"^/pages/(admission|how-apply|fee|financial|degree|geiah)", "admissions"),
    (r"^/pages/(hostel|library|campus-facilities)", "facilities"),
    (r"^/pages/(about|vision|dir-message)|^/about", "about"),
    (r"^/(academic-calendar|code-of-conduct)", "academics"),
    (r"^/(tenders|contact|noticeboard)", "admin"),
    (r"^/(qec-events|cpd-activities|faculty-staff-trainings|outcome_based_education|pages/iqae)", "quality_training"),
    (r"^/(artificial-intelligence|software-engineering|bs-robotics|bs-internet-of-things|bs-|bba|ms-|phd)", "programs"),
]


def category(url: str) -> str:
    path = urlparse(url).path or "/"
    for pat, cat in CATEGORY_RULES:
        if re.search(pat, path):
            return cat
    return "pdf" if path.lower().endswith(".pdf") else "general"


def clean_md(text: str) -> str:
    text = re.sub(r"[ \t]+\n", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def html_to_markdown(html: str) -> tuple[str, str]:
    sel = Selector(html)
    title = (sel.css("title::text").get() or "").strip()
    main = sel.css(".main-content")
    root = main[0] if main else sel.css("body")[0]
    html_main = root.html_content
    html_main = re.sub(r"(?is)<(script|style|noscript|form)\b.*?</\1>", "", html_main)
    html_main = re.sub(r"(?is)<img\b[^>]*>", "", html_main)
    return title, clean_md(md(html_main, heading_style="ATX", strip=["a"] if False else None))


def chunk_markdown(text: str):
    """Heading-aware split into ~CHUNK_WORDS windows; yields (heading_path, chunk_text)."""
    sections, path, buf = [], [], []

    def flush():
        body = "\n".join(buf).strip()
        if body:
            sections.append((" > ".join(path), body))
        buf.clear()

    for line in text.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            flush()
            lvl = len(m.group(1))
            path[:] = path[: lvl - 1] + [m.group(2).strip()]
        else:
            buf.append(line)
    flush()
    for hp, body in sections:
        words = body.split()
        if len(words) <= CHUNK_WORDS:
            yield hp, body
            continue
        i = 0
        while i < len(words):
            yield hp, " ".join(words[i : i + CHUNK_WORDS])
            if i + CHUNK_WORDS >= len(words):
                break
            i += CHUNK_WORDS - OVERLAP_WORDS


def pdf_to_markdown(path: Path) -> tuple[str, str]:
    doc = pymupdf.open(path)
    pages = [f"## Page {n}\n\n{p.get_text().strip()}" for n, p in enumerate(doc, 1) if p.get_text().strip()]
    title = (doc.metadata or {}).get("title") or path.stem
    return title, "\n\n".join(pages)


def main():
    MD.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    seen, n_pages, n_chunks = set(), 0, 0
    with (ROOT / "data" / "chunks.jsonl").open("w") as out:
        for line in (ROOT / "data" / "index.jsonl").open():
            it = json.loads(line)
            if it["status"] != 200:
                continue
            f = RAW / it["file"]
            try:
                title, body = html_to_markdown(f.read_text("utf-8", "ignore")) if it["kind"] == "html" else pdf_to_markdown(f)
            except Exception as e:  # keep going; report
                print("FAIL", it["url"], e)
                continue
            if len(body) < 40:
                continue
            chash = hashlib.sha1(body.encode()).hexdigest()
            if chash in seen:
                continue
            seen.add(chash)
            cat = category(it["url"])
            front = f'---\nurl: {it["url"]}\ntitle: {json.dumps(title, ensure_ascii=False)}\ncategory: {cat}\ncampus: peshawar\nsource_type: {it["kind"]}\nscraped_at: {now}\n---\n\n'
            (MD / f"{f.stem}.md").write_text(front + body, "utf-8")
            n_pages += 1
            for k, (hp, text) in enumerate(chunk_markdown(body)):
                rec = {
                    "id": f"{f.stem}-{k}", "url": it["url"], "title": title, "heading_path": hp,
                    "category": cat, "campus": "peshawar", "source_type": it["kind"],
                    "text": text, "content_hash": chash, "scraped_at": now,
                }
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n_chunks += 1
    print(f"{n_pages} pages, {n_chunks} chunks")


if __name__ == "__main__":
    main()
