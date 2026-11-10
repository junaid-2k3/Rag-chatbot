"""Manual retrieval check: python ingestion/try_queries.py"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
from app.services.embeddings import Embedder  # noqa: E402
from app.services.retrieval import Index  # noqa: E402

QUERIES = [
    "What is the fee structure?", "Is there a hostel and what are the rules?", "How do I apply for admission?",
    "Who is the director of the campus?", "What financial assistance or scholarships are offered?",
    "What degree programs are offered?", "Who are the computer science faculty?", "What is the academic calendar?",
    "What societies can students join?", "Tell me about the library.",
]
emb, idx = Embedder(), Index(ROOT / "index")
for q in QUERIES:
    print(f"\n## {q}")
    for r in idx.search(emb.embed_query(q)):
        print(f'  {r["score"]:.3f} [{r["category"]}] {r["url"].split("pwr.nu.edu.pk")[-1][:45]} | {r["heading_path"][:40]} | {r["text"][:70]!r}')
