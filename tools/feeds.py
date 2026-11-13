"""Read public listings for /scan: arXiv, the Hugging Face Hub and Zenodo.

    uv run --project core python tools/feeds.py [--date YYYY-MM-DD]

Unlike web search these give exact dates and a complete listing for their site.
Configuration: `scan.window_days` and `scan.feeds` in spec.yaml. Writes
candidates/feeds/feeds_<date>.jsonl with one row per item inside the window:
source, url, title, published_at, authors_or_owner, matched. Titles and URLs only; no
abstract or page text is stored (CLAUDE.md rule 9). Requests carry no personal details.
"""

from __future__ import annotations

import argparse
import json
import re
import time
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "forecast-claims-scan/0.1"}
ATOM = "{http://www.w3.org/2005/Atom}"


def get(url: str, params: dict) -> requests.Response:
    for attempt in range(3):
        r = requests.get(url, params=params, headers=UA, timeout=60)
        if r.status_code == 200:
            return r
        time.sleep(5 * (attempt + 1))
    r.raise_for_status()
    return r


def arxiv(cfg: dict, start: date, end: date) -> list[dict]:
    cats = " OR ".join(f"cat:{c}" for c in cfg["categories"])
    must = " AND ".join(f'all:"{w}"' for w in cfg["must_match"])
    window = f"submittedDate:[{start:%Y%m%d}0000 TO {end:%Y%m%d}2359]"
    query = f"({cats}) AND {must} AND {window}"
    rows, offset, page = [], 0, 200
    while True:
        r = get(
            "https://export.arxiv.org/api/query",
            {
                "search_query": query,
                "start": offset,
                "max_results": page,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            },
        )
        entries = ET.fromstring(r.text).findall(f"{ATOM}entry")
        for e in entries:
            title = " ".join(e.findtext(f"{ATOM}title", "").split())
            text = (title + " " + e.findtext(f"{ATOM}summary", "")).lower()
            matched = [w for w in cfg["any_of"] if w in text]
            if not matched:
                continue
            abs_url = re.sub(r"v\d+$", "", e.findtext(f"{ATOM}id", "")).replace(
                "http://", "https://"
            )
            rows.append(
                {
                    "source": "arxiv",
                    "url": abs_url,
                    "title": title,
                    "published_at": e.findtext(f"{ATOM}published", "")[:10],  # first version
                    "authors_or_owner": e.findtext(f"{ATOM}author/{ATOM}name", ""),
                    "matched": matched,
                }
            )
        if len(entries) < page or offset >= 2000:
            return rows
        offset += page
        time.sleep(3)  # arXiv asks for a pause between calls


def huggingface(cfg: dict, start: date, end: date) -> list[dict]:
    r = get(
        "https://huggingface.co/api/models",
        {"pipeline_tag": cfg["pipeline_tag"], "sort": "createdAt", "direction": -1, "limit": 500},
    )
    rows = []
    for m in r.json():
        created = (m.get("createdAt") or "")[:10]
        if created and start.isoformat() <= created <= end.isoformat():
            rows.append(
                {
                    "source": "huggingface",
                    "url": f"https://huggingface.co/{m['id']}",
                    "title": m["id"],
                    "published_at": created,
                    "authors_or_owner": m["id"].split("/")[0],
                    "matched": [f"downloads={m.get('downloads', 0)}", f"likes={m.get('likes', 0)}"],
                }
            )
    return rows


def zenodo(cfg: dict, start: date, end: date) -> list[dict]:
    rows, seen = [], set()
    for q in cfg["queries"]:
        for page in range(1, 5):  # unauthenticated requests are limited to 25 per page
            r = get(
                "https://zenodo.org/api/records",
                {
                    "q": f"({q}) AND publication_date:[{start.isoformat()} TO {end.isoformat()}]",
                    "sort": "mostrecent",
                    "size": 25,
                    "page": page,
                },
            )
            hits = r.json().get("hits", {}).get("hits", [])
            for h in hits:
                url = f"https://zenodo.org/records/{h['id']}"
                if url in seen:
                    continue
                seen.add(url)
                meta = h.get("metadata", {})
                creators = meta.get("creators") or [{}]
                rows.append(
                    {
                        "source": "zenodo",
                        "url": url,
                        "title": " ".join((meta.get("title") or "").split()),
                        "published_at": meta.get("publication_date", "unknown"),
                        "authors_or_owner": creators[0].get("name", ""),
                        "matched": [q],
                    }
                )
            time.sleep(1)
            if len(hits) < 25:
                break
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=date.today().isoformat())
    a = ap.parse_args()
    scan = yaml.safe_load((ROOT / "spec.yaml").read_text())["scan"]
    end = date.fromisoformat(a.date)
    start = end - timedelta(days=scan["window_days"])
    rows = []
    for name, fn in (("arxiv", arxiv), ("huggingface", huggingface), ("zenodo", zenodo)):
        try:
            got = fn(scan["feeds"][name], start, end)
        except (requests.RequestException, ET.ParseError) as e:  # report, do not hide
            print(f"{name}: FAILED ({type(e).__name__})")
            continue
        print(f"{name}: {len(got)} items in {start} .. {end}")
        rows += got
    out = ROOT / "candidates" / "feeds" / f"feeds_{end.isoformat()}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print("wrote", out.relative_to(ROOT), len(rows), "rows")


if __name__ == "__main__":
    main()
