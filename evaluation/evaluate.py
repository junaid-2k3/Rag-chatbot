"""RAG evaluation.

  python evaluation/evaluate.py --retrieval-only [--index DIR]   # Recall@5, Precision@5, MRR (no LLM)
  python evaluation/evaluate.py                                   # + answers, refusal checks, Gemini-judged scores

Relevance is page-level: a retrieved chunk is relevant if its URL contains any `relevant_urls` string.
Recall@5 = fraction of answerable questions with >=1 relevant chunk in the top 5 (hit rate).
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
from app import config  # noqa: E402
from app.services import llm, rag  # noqa: E402
from app.services.embeddings import Embedder  # noqa: E402
from app.services.retrieval import Index  # noqa: E402

JUDGE_SYSTEM = """You grade a RAG chatbot answer. Reply with JSON only:
{"faithfulness": 1-5, "relevancy": 1-5, "keys_present": true|false}
faithfulness: 5 = every claim is supported by the context, 1 = mostly unsupported or invented.
relevancy: 5 = directly and fully answers the question, 1 = off-topic.
keys_present: true if every expected fact is stated in the answer."""
PAUSE = 4  # seconds between LLM calls, free-tier rate limits


def load(name):
    return [json.loads(line) for line in (ROOT / "evaluation" / name).open()]


def judge(question, answer, contexts, keys):
    text = f"Question: {question}\nExpected facts: {keys}\n\nContext:\n" + "\n---\n".join(contexts) + f"\n\nAnswer:\n{answer}"
    raw = llm.generate(JUDGE_SYSTEM, [{"role": "user", "parts": [{"text": text}]}], max_tokens=100, temperature=0)
    m = re.search(r"\{.*\}", raw, re.S)
    return json.loads(m.group(0)) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--retrieval-only", action="store_true")
    ap.add_argument("--index", default=str(config.INDEX_DIR))
    ap.add_argument("--out", default=str(ROOT / "evaluation" / "results.json"))
    args = ap.parse_args()

    questions = {q["id"]: q["question"] for q in load("questions.jsonl")}
    truth = load("ground_truth.jsonl")
    emb, index = Embedder(), Index(Path(args.index))
    rows = []
    for t in truth:
        q = questions[t["id"]]
        hits = index.search(emb.embed_query(q), config.TOP_K)
        rel = [any(u in h["url"] for u in t["relevant_urls"]) for h in hits]
        row = {"id": t["id"], "question": q, "answerable": t["answerable"], "top1_score": round(hits[0]["score"], 3)}
        if t["answerable"]:
            first = next((i for i, r in enumerate(rel) if r), None)
            row.update(hit=first is not None, precision=sum(rel) / len(rel), rr=1 / (first + 1) if first is not None else 0.0)
        if not args.retrieval_only:
            try:
                r = rag.answer(q)
                row.update(answer=r["answer"], refused=not r["sources"])
                if t["answerable"] and not row["refused"]:
                    row["judge"] = judge(q, r["answer"], [h["text"] for h in hits], t["answer_keys"])
                    time.sleep(PAUSE)
                time.sleep(PAUSE)
            except llm.LLMUnavailable as e:
                row["error"] = str(e)
        rows.append(row)
        print(row["id"], {k: v for k, v in row.items() if k in ("hit", "rr", "refused", "judge", "error")})

    ans = [r for r in rows if r["answerable"]]
    summary = {
        "index": args.index, "n_answerable": len(ans),
        "recall@5": sum(r["hit"] for r in ans) / len(ans),
        "precision@5": sum(r["precision"] for r in ans) / len(ans),
        "mrr": sum(r["rr"] for r in ans) / len(ans),
    }
    if not args.retrieval_only:
        neg = [r for r in rows if not r["answerable"] and "error" not in r]
        judged = [r["judge"] for r in ans if r.get("judge")]
        summary.update(
            correct_refusals=f'{sum(r["refused"] for r in neg)}/{len(neg)}',
            false_refusals=f'{sum(r.get("refused", False) for r in ans)}/{len(ans)}',
            faithfulness=sum(j["faithfulness"] for j in judged) / max(len(judged), 1),
            relevancy=sum(j["relevancy"] for j in judged) / max(len(judged), 1),
            keys_present=f'{sum(bool(j["keys_present"]) for j in judged)}/{len(judged)}',
            llm_errors=sum("error" in r for r in rows),
        )
    Path(args.out).write_text(json.dumps({"summary": summary, "rows": rows}, indent=2, ensure_ascii=False))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
