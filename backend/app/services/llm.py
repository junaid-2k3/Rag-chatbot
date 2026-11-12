"""Minimal Gemini REST client (no SDK, keeps the Lambda image small)."""
import logging
import time

import httpx

from .. import config

log = logging.getLogger("llm")

URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
RETRYABLE = {429, 500, 502, 503, 504}


class LLMUnavailable(Exception):
    """Quota exhausted or API down after retries and fallback."""


def _call(model: str, system: str, contents: list[dict], max_tokens: int, temperature: float) -> str:
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": contents,
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
    }
    r = httpx.post(URL.format(model=model), json=body, headers={"x-goog-api-key": config.GEMINI_API_KEY}, timeout=30)
    if r.status_code != 200:
        raise _HTTPError(r.status_code)
    cands = r.json().get("candidates") or []
    parts = cands[0].get("content", {}).get("parts") if cands else None
    if not parts:
        raise _HTTPError(0)  # blocked or empty
    return "".join(p.get("text", "") for p in parts).strip()


class _HTTPError(Exception):
    def __init__(self, status: int):
        self.status = status


def generate(system: str, contents: list[dict], max_tokens: int = 700, temperature: float = 0.2) -> str:
    """Try primary model twice, then the fallback model once. Raise LLMUnavailable if all fail."""
    attempts = [config.GEMINI_MODEL, config.GEMINI_MODEL, config.GEMINI_FALLBACK_MODEL]
    for n, model in enumerate(attempts):
        t0 = time.monotonic()
        try:
            text = _call(model, system, contents, max_tokens, temperature)
            log.info("gemini model=%s ok %.1fs", model, time.monotonic() - t0)
            return text
        except _HTTPError as e:
            log.warning("gemini model=%s status=%s %.1fs", model, e.status, time.monotonic() - t0)
            if e.status not in RETRYABLE and e.status != 0:
                raise LLMUnavailable(f"Gemini error {e.status}") from e
        except httpx.HTTPError as e:
            log.warning("gemini model=%s %s %.1fs", model, type(e).__name__, time.monotonic() - t0)
        if n < len(attempts) - 1:
            time.sleep(1.5)
    raise LLMUnavailable("Gemini is busy or the free quota is used up")
