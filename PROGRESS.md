# Progress

## Phase 0 — Scraping (done)
- [x] Crawl pwr.nu.edu.pk with Scrapling spider
- [x] Convert to Markdown + `data/chunks.jsonl`

## Phase 1 — Local RAG pipeline (done)
- [x] uv venv (Python 3.12) + install deps
- [x] bge-small ONNX (prebuilt from HF, in `models/bge-small`)
- [x] Token-based chunking (450 / 80), 2020 PDFs excluded
- [x] Embed + normalize -> `index/` (1,307 chunks, 384 dims, ~7.5 min on CPU)
- [x] Cosine top-5 retrieval; 10 hand queries checked (`ingestion/try_queries.py`)
- Known weak spots (for Phase 3): "CS faculty" ranks society pages first; many web pages have generic title "FAST - NUCES Peshawar"; breadcrumbs inside chunks

## Phase 2 — LLM integration (done)
- [x] **You:** put `GEMINI_API_KEY` in `.env`
- [x] Verify Gemini model ID + limits: `gemini-3.1-flash-lite` exists but returned 503 "high demand" on every try; auto-fallback to `gemini-3.5-flash-lite` (works). Override with `GEMINI_MODEL` / `GEMINI_FALLBACK_MODEL`
- [x] Prompt builder, citations ([n] -> title + URL, page for PDFs), 4-turn history with follow-up query rewrite
- [x] Not-found / out-of-scope refusal (score < 0.60 skips the LLM; prompt returns NOT_FOUND; other-campus questions answered "Peshawar only")
- [x] Error + rate-limit handling (2 tries primary + 1 fallback, then `LLMUnavailable`); CLI: `.venv/bin/python backend/cli.py`
- Known gaps for Phase 3: "Who is the director?" refuses (name is only a signature under Director Message); free-tier daily quota not yet measured

## Phase 3 — Evaluation
- [ ] Draft ~30 questions + ground truth (**You:** review)
- [ ] Recall@5, Precision@5, MRR
- [ ] Gemini-judge faithfulness / relevancy
- [ ] Try one alternative chunk size; write report

## Phase 4 — FastAPI backend
- [ ] `/chat` endpoint + schemas + validation
- [ ] Tested: normal, empty, oversize, off-topic

## Phase 5 — Astro frontend
- [ ] **You:** create public GitHub repo, enable Pages, `gh auth login`
- [ ] Chat UI, source cards, loading/error states
- [ ] Light/dark + mobile check

## Phase 6 — AWS deploy
- [ ] **You:** AWS account, MFA, $1 budget alert, IAM, install AWS CLI, `aws configure`
- [ ] Private S3 bucket + index upload
- [ ] Lambda container image (Docker) + Function URL
- [ ] Concurrency cap, CORS, env var secret
- [ ] GitHub Pages deploy; end-to-end test

## Phase 7 — Docs
- [ ] README, architecture diagram, eval results, latency numbers
