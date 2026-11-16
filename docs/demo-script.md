# Demo script (about 90 seconds)

Record the browser at https://junaid-2k3.github.io/Rag-chatbot/ . Open the page once beforehand so the backend is warm (the first question after idle can take 5-10 s).

1. **Open the page (5 s).** Say what it is: a chatbot for FAST-NUCES Peshawar that answers only from the campus website and shows its sources.
2. **Click "How much is the admission fee?" (10 s).** Point at the blue `[1]` chip in the answer and the source card below it.
3. **Click the `[1]` chip (5 s).** The matching source card is highlighted. Click the card to open the original page.
4. **Ask "When do Fall 2026 classes start?", then "and when is the first sessional exam?" (20 s).** The second question only works because the bot remembers the previous turn.
5. **Ask "who is the director of fast nuces peshawar" (10 s).** The answer cites a source card.
6. **Ask "What is the capital of France?" (10 s).** It refuses and points to nu.edu.pk instead of answering from general knowledge.
7. **Toggle dark mode and narrow the window or open it on a phone (10 s).**
8. **Open the GitHub README (15 s).** Show the architecture diagram, the evaluation table (Recall@5 0.96, MRR 0.87, 0 false refusals out of 26) and the Known limitations section.

Do not show the AWS console or `.env`.
