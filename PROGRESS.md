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

## Phase 3 — Evaluation (done)
- [x] Draft 31 questions + ground truth (**You:** review `evaluation/ground_truth.jsonl`, especially q25 director)
- [x] Recall@5 0.92, Precision@5 0.47, MRR 0.82
- [x] Gemini-judge faithfulness 4.83 / relevancy 5.0; refusals 6/6 correct, 1/25 false
- [x] Chunk size compared (450/80 vs 250/40) + boilerplate cleaning; shipped 250/40 (`evaluation/report.md`)
- Open: stale 2021/2022 calendar PDFs still indexed (your call); campus area/address retrieval misses

## Phase 4 — FastAPI backend (done)
- [x] Stale 2021/2022 calendars, timetables, date sheet excluded from index (1,392 chunks; Recall@5 0.92, MRR 0.83)
- [x] `POST /chat` + `GET /health`, pydantic schemas, 503 when Gemini is down, CORS via `ALLOWED_ORIGINS`
- [x] Input limits: question 1-500 chars, history max 8 messages of 2,000 chars
- [x] 14 pytest tests (`.venv/bin/python -m pytest backend/tests`); live curl checked: normal, follow-up, off-topic, empty, oversize
- Run: `.venv/bin/python -m uvicorn app.main:app --app-dir backend --port 8000` (docs at /docs)

## Phase 5 — Astro frontend (done locally; Pages deploy is Phase 6)
- [x] Astro 7 + Vite project in `frontend/`, IBM Plex Sans (self-hosted), neutral blue-and-white theme, light/dark toggle (saved, follows system by default)
- [x] Components: ChatWindow, Message, ChatInput, SourceCard; `services/api.ts`; safe answer renderer `lib/render.ts`
- [x] Inline `[n]` citation chips jump to the matching source card (backend now renumbers citations to match the sources list)
- [x] Loading, error + "Try again", empty state with 4 starter questions, 500-char counter, Enter to send
- [x] Verified in Chromium (Playwright): desktop, 360px and 390px mobile with no horizontal scroll, dark mode, follow-up sends history, mocked 503 -> retry, XSS probe does not execute
- [x] Tests: `pnpm test` (5, renderer) in `frontend/`; backend now 17
- [ ] **You:** create public GitHub repo, enable Pages (source: GitHub Actions), `gh auth login` (needed for Phase 6 deploy)
- Run locally: API `.venv/bin/python -m uvicorn app.main:app --app-dir backend --port 8000`, then `cd frontend && pnpm dev` (open http://localhost:4321). API URL is `PUBLIC_API_URL` (default http://localhost:8000)

## Phase 6 — AWS deploy (done)
- [x] Decisions: zip + model fetched from S3 to /tmp; region **ap-southeast-2 (Sydney)** (new-style Free plan accounts are locked to one region chosen from the contact country; other regions are denied by AWS-managed SCPs); reserved concurrency 3 (quota 400); repo `junaid-2k3/Rag-chatbot`
- [x] Lambda handler (Mangum, Function URL), S3 asset loader, Swagger off in production, CloudFormation stack `fast-pwr-chatbot`
- [x] Deployed: https://nsgcu3ywayyk3gagfwq6thvkru0htuyi.lambda-url.ap-southeast-2.on.aws/ (1024 MB, 90 s timeout, logs kept 14 days, private bucket `fast-pwr-chatbot-923484439416-ap-southeast-2`)
- [x] Frontend live at https://junaid-2k3.github.io/Rag-chatbot/ (repo variable `PUBLIC_API_URL` set; Pages workflow green)
- [x] End-to-end in a browser on the live site: answers, citations, follow-up, no CORS errors
- [x] Latency measured: cold start about 1.5 s init + 2.5 s first-request (S3 download + load); warm Lambda 1-2 s plus the Gemini call (median 1.3 s, spikes up to ~14 s); about 0.7 s network from Pakistan to Sydney
- [x] Fixes found during deploy: readable PDF titles, one card per source, fewer citation markers, Gemini timeout 30 -> 15 s, app logs now reach CloudWatch
- [ ] **You:** open the AWS Billing console and confirm credits are being used as expected; do not create a "spend limit" in AWS Settings (near the limit AWS denies Lambda/CloudFormation)
- Known limits: follow-up "and the admission fee?" after a hostel question is rewritten to a hostel query and returns the Rs 3,000 applicant fee; Gemini free tier can spike to 10+ s

## Maintenance log
- 2026-11-16: "who is the director" was refused. Fixed by dropping the generic title from embedded text, removing <40-character chunks and adding `data/curated/director.md`. Recall@5 0.88 -> 0.96, MRR 0.80 -> 0.87 (26 questions). Deploy now sets `INDEX_VERSION` so new indexes always reach running containers. See `evaluation/report.md`.

## Phase 7 — Documentation and polish (done)
- [x] README: overview, two architecture diagrams (Mermaid, render checked), step-by-step request flow, stack, layout, local run, deploy, logs
- [x] Evaluation results published: README table + `evaluation/report.md` (Recall@5 0.96, Precision@5 0.52, MRR 0.87; refusals 6/6, false refusals 0/26)
- [x] Latency numbers published (cold start, warm, Gemini median/spikes, network)
- [x] Design decisions, limits/security and known limitations documented
- [x] Structured logging + CloudWatch (14-day retention), input-size limits and concurrency cap (done in Phases 4-6)
- [x] Caching: model, index and S3 downloads are cached per Lambda container; no answer cache (not added on purpose: questions rarely repeat and it would serve stale answers)
- [ ] Not done: per-IP rate limiting (needs API Gateway/WAF or a database, outside the $0 plan)
- [ ] **You:** record the demo (script in `docs/demo-script.md`)
- [ ] **You:** open the AWS Billing console and confirm credits are being used as expected
