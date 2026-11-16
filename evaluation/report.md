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

## Update 2026-11-16: director question, cleaner embeddings

Reported failure: "who is the director of fast nuces peshawar" was refused. The answer exists in the corpus (his faculty profile says "Director Campus"), but short society-profile fragments such as "Advisor" ranked above it.

Cause (measured): every scraped page has the generic title "FAST - NUCES Peshawar", and it was embedded as a prefix on every chunk. A 7-character "Advisor" chunk scored 0.81 against that question with the prefix and 0.56 without. 215 of 1,393 chunks had under 40 characters of text.

Changes: generic titles are no longer embedded (PDFs use their file name instead of a hash), chunks under 40 characters are dropped, and a hand-written fact page `data/curated/director.md` is indexed with the scraped pages.

| Index | Chunks | Questions | Recall@5 | Precision@5 | MRR |
|---|---|---|---|---|---|
| Before (shipped 2026-11-12) | 1393 | 26 | 0.88 | 0.48 | 0.80 |
| After | 1178 | 26 | **0.96** | **0.52** | **0.87** |

Full pipeline after: correct refusals 6/6, false refusals 0/26 (was 1/25), faithfulness 5.0, relevancy 5.0, expected facts 25/26 (q22 expects the word "bus"; the answer says "transport", so that is a weak ground-truth key, not a wrong answer).

Caveats: q32 was added after the failure was reported, and the curated chunk targets it, so that one question measures the fix, not generalisation. Without it, the cleaner embeddings alone are what moved the other numbers. The only remaining retrieval miss is q20 (campus address). The 0.60 refusal cutoff still separates nothing cleanly (answerable minimum 0.68, unanswerable maximum 0.73), so refusals of off-topic questions mostly rely on the LLM.
