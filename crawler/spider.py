"""Crawl pwr.nu.edu.pk with a Scrapling Spider; save raw HTML/PDF to data/raw and an index.jsonl."""
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urldefrag, urlparse

from scrapling.fetchers import FetcherSession
from scrapling.spiders import Request, Spider

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
HOST = "pwr.nu.edu.pk"
UA = "UniversityChatbotResearchBot/1.0 (RAG dataset for FAST-NUCES Peshawar; contact: sajidislam.fast@gmail.com)"

SKIP_EXT = re.compile(
    r"\.(jpe?g|png|gif|svg|webp|ico|css|js|woff2?|ttf|eot|mp4|mp3|zip|rar|docx?|xlsx?|pptx?)(\?|$)", re.I
)
SKIP_PATH = re.compile(r"/(login|logout|signin|wp-admin)\b", re.I)


def norm(url: str) -> str | None:
    url, _ = urldefrag(url)
    p = urlparse(url)
    if p.scheme not in ("http", "https") or p.netloc.lower().removeprefix("www.") != HOST:
        return None
    if SKIP_EXT.search(url) or SKIP_PATH.search(p.path):
        return None
    return f"https://{HOST}{p.path or '/'}" + (f"?{p.query}" if p.query else "")


class PwrSpider(Spider):
    name = "pwr"
    start_urls = [f"https://{HOST}/"]
    allowed_domains = {HOST}
    robots_txt_obey = False  # user-approved override; site robots.txt disallows generic bots
    concurrent_requests = 4
    download_delay = 0.5

    def configure_sessions(self, manager):
        manager.add(
            "default",
            FetcherSession(impersonate=None, stealthy_headers=False, headers={"User-Agent": UA},
                           retries=3, retry_delay=2, timeout=30),
        )

    async def parse(self, response):
        url = norm(str(response.url)) or str(response.url)
        ctype = (response.headers.get("content-type") or response.headers.get("Content-Type") or "").lower()
        h = hashlib.sha1(url.encode()).hexdigest()[:16]
        RAW.mkdir(parents=True, exist_ok=True)
        if "pdf" in ctype or urlparse(url).path.lower().endswith(".pdf"):
            (RAW / f"{h}.pdf").write_bytes(response.body)
            yield {"url": url, "kind": "pdf", "file": f"{h}.pdf", "status": response.status}
            return
        if "html" not in ctype and ctype:
            return
        (RAW / f"{h}.html").write_bytes(response.body)
        yield {
            "url": url, "kind": "html", "file": f"{h}.html", "status": response.status,
            "title": (response.css("title::text").get() or "").strip(),
            "text_len": len(response.get_all_text()) if hasattr(response, "get_all_text") else 0,
        }
        for href in response.css("a::attr(href)").getall():
            if href.lower().startswith(("mailto:", "tel:", "javascript:")):
                continue
            target = norm(urljoin(f"https://{HOST}/", href))
            if target:
                yield Request(target, sid="default", callback=self.parse)


if __name__ == "__main__":
    out = ROOT / "data" / "index.jsonl"
    spider = PwrSpider(crawldir=str(ROOT / "crawl_state"))
    result = spider.start()
    with out.open("w") as f:
        for item in result.items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(result.stats)
    print(f"{len(result.items)} items -> {out}")
