import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.main import app  # noqa: E402
from app.services import llm, rag  # noqa: E402

client = TestClient(app)
OK = {"answer": "Rs 30,000 [1]", "found": True, "query": "q",
      "sources": [{"title": "Fee Structure", "heading": "Fee Structure > Admission Fee", "url": "https://pwr.nu.edu.pk/pages/fee-structure", "page": None, "score": 0.7}]}


@pytest.fixture
def fake_rag(monkeypatch):
    calls = []
    monkeypatch.setattr(rag, "answer", lambda q, h: calls.append((q, h)) or OK)
    return calls


def test_chat_ok_strips_and_hides_internals(fake_rag):
    r = client.post("/chat", json={"question": "  admission fee?  ", "history": []})
    assert r.status_code == 200
    body = r.json()
    assert body["found"] is True and body["sources"][0]["url"].endswith("fee-structure")
    assert "score" not in body["sources"][0] and "query" not in body
    assert fake_rag[0][0] == "admission fee?"


def test_history_passed_through(fake_rag):
    h = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
    assert client.post("/chat", json={"question": "and the fee?", "history": h}).status_code == 200
    assert fake_rag[0][1] == h


@pytest.mark.parametrize("payload", [
    {"question": ""},
    {"question": "   "},
    {"question": "x" * 501},
    {},
    {"question": "ok", "history": [{"role": "system", "content": "x"}]},
    {"question": "ok", "history": [{"role": "user", "content": ""}]},
    {"question": "ok", "history": [{"role": "user", "content": "y" * 2001}]},
    {"question": "ok", "history": [{"role": "user", "content": "a"}] * 9},
])
def test_invalid_input_rejected(fake_rag, payload):
    assert client.post("/chat", json=payload).status_code == 422
    assert fake_rag == []  # never reaches the LLM


def test_boundary_500_chars_ok(fake_rag):
    assert client.post("/chat", json={"question": "x" * 500}).status_code == 200


def test_llm_down_gives_503(monkeypatch):
    def boom(q, h):
        raise llm.LLMUnavailable("quota")
    monkeypatch.setattr(rag, "answer", boom)
    r = client.post("/chat", json={"question": "fee?"})
    assert r.status_code == 503 and "busy" in r.json()["detail"]


def test_cors_allowed_and_blocked_origin(fake_rag):
    ok = client.options("/chat", headers={"Origin": "http://localhost:4321", "Access-Control-Request-Method": "POST"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:4321"
    bad = client.options("/chat", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in bad.headers


def test_health():
    assert client.get("/health").json() == {"status": "ok"}
