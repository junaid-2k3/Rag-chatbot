"""Terminal chatbot: python backend/cli.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from app import config  # noqa: E402
from app.services import llm, rag  # noqa: E402

history: list[dict] = []
print("FAST Peshawar assistant. Ctrl-D to quit.")
while True:
    try:
        q = input("\nyou> ").strip()[: config.MAX_QUESTION_CHARS]
    except EOFError:
        break
    if not q:
        continue
    try:
        r = rag.answer(q, history)
    except llm.LLMUnavailable as e:
        print(f"bot> Service is busy right now ({e}). Please try again shortly.")
        continue
    print(f"bot> {r['answer']}")
    for i, s in enumerate(r["sources"], 1):
        print(f"   - {s['title']} ({s['url']}{', p.' + str(s['page']) if s['page'] else ''})")
    history += [{"role": "user", "content": q}, {"role": "assistant", "content": r["answer"]}]
