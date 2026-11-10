# pwr.nu.edu.pk corpus for RAG

Run from this directory:

    python3 -I crawler/spider.py     # crawl -> data/raw, data/index.jsonl (resumable via crawl_state/)
    python3 -I crawler/process.py    # -> data/markdown/*.md, data/chunks.jsonl

Chunk fields: id, url, title, heading_path, category, campus, source_type, text, content_hash, scraped_at.

Note: the site's robots.txt disallows generic bots; the crawl overrides it by user decision, with an identifying User-Agent, 4 concurrent requests and 0.5s delay.
