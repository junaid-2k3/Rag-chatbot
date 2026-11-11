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

## Phase 6 — AWS deploy (prep done, deploy waiting on your accounts)
- [x] Decisions: zip + model fetched from S3 to /tmp, region ap-south-1, no reserved concurrency (Gemini quota + budget alert + input limits instead), repo `fast-peshawar-chatbot`
- [x] Lambda handler (Mangum, Function URL), S3 asset loader, Swagger off in production
- [x] `infrastructure/build_zip.sh` (165 MB unzipped, 53 MB zipped; uploaded via S3), `template.yaml` (cfn-lint clean), `deploy.sh`, `destroy.sh`
- [x] `.github/workflows/deploy-frontend.yml` (Pages; reads repo variable `PUBLIC_API_URL`)
- [x] Verified locally: built zip invoked with Function URL events (CORS allow/deny, docs 404, refusal, real Gemini answer); 19 backend tests
- [ ] **You:** `gh auth login`
- [ ] **You:** AWS account, MFA on root, $1 budget alert, IAM user for CLI, install AWS CLI v2, `aws configure`
- [ ] Create public repo `fast-peshawar-chatbot`, push (rename branch to `main`), enable Pages (source: GitHub Actions)
- [ ] Run `ALLOWED_ORIGINS=https://<user>.github.io ./infrastructure/deploy.sh` (untested until AWS exists)
- [ ] Set repo variable `PUBLIC_API_URL` = Function URL, run the Pages workflow
- [ ] End-to-end test from the live site; measure cold and warm latency; check billing page

## Phase 7 — Docs
- [ ] README, architecture diagram, eval results, latency numbers
