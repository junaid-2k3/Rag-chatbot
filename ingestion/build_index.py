"""One-time index build: data/markdown/*.md -> index/{vectors.npy,chunks.jsonl,manifest.json}.

Chunks are 450 tokens with 80 overlap, split inside heading sections (bge tokenizer counts tokens).
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
from app.services.embeddings import Embedder  # noqa: E402

MD, OUT = ROOT / "data" / "markdown", ROOT / "index"
CHUNK_TOKENS, OVERLAP_TOKENS = 450, 80
EXCLUDE_URL = ("Prospectus-2020.pdf", "student-handbook-2020.pdf")  # outdated, per user decision


def parse(path: Path):
    raw = path.read_text("utf-8")
    _, front, body = raw.split("---\n", 2)
    meta = {}
    for line in front.splitlines():
        k, _, v = line.partition(": ")
        meta[k] = json.loads(v) if v.startswith('"') else v
    return meta, body.strip()


def sections(body: str):
    """Yield (heading_path, text) per heading section."""
    path, buf = [], []
    for line in body.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            if "".join(buf).strip():
                yield " > ".join(path), "\n".join(buf).strip()
            buf = []
            lvl = len(m.group(1))
            path = path[: lvl - 1] + [m.group(2).strip()]
        else:
            buf.append(line)
    if "".join(buf).strip():
        yield " > ".join(path), "\n".join(buf).strip()


def token_windows(tok, text: str):
    enc = tok.encode(text, add_special_tokens=False)
    n, step = len(enc.ids), CHUNK_TOKENS - OVERLAP_TOKENS
    start = 0
    while True:
        end = min(start + CHUNK_TOKENS, n)
        yield text[enc.offsets[start][0] : enc.offsets[end - 1][1]]
        if end >= n:
            return
        start += step


def main():
    emb = Embedder()
    tok = emb.tok
    tok.no_truncation(), tok.no_padding()  # for counting/offsets
    chunks = []
    for f in sorted(MD.glob("*.md")):
        meta, body = parse(f)
        if meta["url"].endswith(EXCLUDE_URL):
            continue
        for hp, text in sections(body):
            for piece in token_windows(tok, text):
                page = re.search(r"Page (\d+)", hp)
                chunks.append({
                    "id": f"{f.stem}-{len(chunks)}", "url": meta["url"], "title": meta["title"],
                    "heading_path": hp, "category": meta["category"], "source_type": meta["source_type"],
                    "page": int(page.group(1)) if page and meta["source_type"] == "pdf" else None,
                    "text": piece,
                })
    tok.enable_truncation(max_length=512), tok.enable_padding()
    inputs = [f'{c["title"]} | {c["heading_path"]}\n{c["text"]}' for c in chunks]
    vecs = emb.embed_documents(inputs)
    OUT.mkdir(exist_ok=True)
    np.save(OUT / "vectors.npy", vecs)
    with (OUT / "chunks.jsonl").open("w") as fh:
        for c in chunks:
            fh.write(json.dumps(c, ensure_ascii=False) + "\n")
    (OUT / "manifest.json").write_text(json.dumps({
        "model": "BAAI/bge-small-en-v1.5", "dim": int(vecs.shape[1]), "count": len(chunks),
        "chunk_tokens": CHUNK_TOKENS, "overlap_tokens": OVERLAP_TOKENS,
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }, indent=2))
    print(f"{len(chunks)} chunks, vectors {vecs.shape}")


if __name__ == "__main__":
    main()
