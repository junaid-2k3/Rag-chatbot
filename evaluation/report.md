# Evaluation report

Set: 31 questions (25 answerable, 6 that must be refused), drafted from the scraped pages by the assistant; ground truth is page-level (`evaluation/ground_truth.jsonl`). **Not yet reviewed by the project owner.** With 25 questions, one question is 4 points of Recall, so treat differences of one question as noise.

## Retrieval (top 5, no LLM)

| Index | Chunks | Recall@5 | Precision@5 | MRR |
|---|---|---|---|---|
| Baseline: 450/80 tokens, raw text | 1307 | 0.80 | 0.45 | 0.70 |
| + strip breadcrumbs / "auto-retrieved" boilerplate | 1254 | 0.88 | 0.46 | 0.76 |
| **+ 250/40 tokens (shipped)** | 1430 | **0.92** | **0.47** | **0.82** |

Precision@5 is capped low by design: most questions have one relevant page, so at most a few of the 5 chunks can match.

## Full pipeline on the shipped index (Gemini answers, Gemini judge)

| Metric | Result |
|---|---|
| Correct refusals (unanswerable) | 6/6 |
| False refusals (answerable) | 1/25 (q18 campus area/location) |
| Faithfulness (1-5) | 4.83 |
| Relevancy (1-5) | 5.00 |
| Expected facts present | 23/24 judged |
| LLM errors | 0 |

## Observations
- Cleaning page boilerplate helped most: tiny pages (admission schedule, contact) were one chunk dominated by breadcrumbs.
- Smaller chunks helped, since most answers are single table rows or sentences.
- Still missed: q18 (campus area, location) and q20 (address, on `/contact/`) in retrieval. Those facts sit in short pages next to much longer pages.
- q25 "Who is the director?": the bot answers "Dr. Omar Usman Khan". The corpus only shows his name as the signature under "Director Message", so this is an inference. The judge scored it faithfulness 1 and flagged the key missing; the answer text does contain the name, so that row is judge noise, but the inference itself is not stated in any page. Verify against the live site.
- Stale 2021/2022 academic-calendar PDFs and timetables are still indexed and compete with the live calendar (q09 ranks 3rd). Excluding them is a data decision for the owner (not done).
- Judge is the same model family as the answerer and rates generously; faithfulness scores are an upper bound.
