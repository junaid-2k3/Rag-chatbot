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

## Phase 2 — LLM integration
- [ ] **You:** put `GEMINI_API_KEY` in `.env`
- [ ] Verify Gemini model ID + free-tier limits
- [ ] Prompt builder, citations, 4-turn history
- [ ] Not-found / out-of-scope refusal
- [ ] Error + rate-limit handling; CLI chatbot works

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
