"""Read public listings for /scan: arXiv, the Hugging Face Hub and Zenodo.

    uv run --project core python tools/feeds.py [--date YYYY-MM-DD]

Unlike web search these give exact dates and a complete listing for their site.
Configuration: `scan.window_days` and `scan.feeds` in spec.yaml. Writes
candidates/feeds/feeds_<date>.jsonl with one row per item inside the window:
source, url, title, published_at, authors_or_owner, matched. That file holds titles and
URLs only and is committed. Abstracts (arXiv) and descriptions (Zenodo) go to
data/feeds/abstracts_<date>.jsonl, which is git-ignored: other people's text is read
locally and never committed (CLAUDE.md rule 9). Requests carry no personal details.

    uv run --project core python tools/feeds.py --show <url> [<url> ...]   # print abstracts
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
        time.sleep(20 * (attempt + 1))  # arXiv and Zenodo rate-limit bursts
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
                    "abstract": " ".join(e.findtext(f"{ATOM}summary", "").split()),
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
                        "abstract": " ".join(
                            re.sub(r"<[^>]+>", " ", meta.get("description") or "").split()
                        )[:3000],
                    }
                )
            time.sleep(1)
            if len(hits) < 25:
                break
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=date.today().isoformat())
    ap.add_argument("--show", nargs="+", metavar="URL", help="print stored abstracts")
    a = ap.parse_args()
    local = ROOT / "data" / "feeds" / f"abstracts_{a.date}.jsonl"
    if a.show:
        if not local.exists():
            raise SystemExit(f"{local.relative_to(ROOT)} not found; run without --show first")
        by_url = {r["url"]: r for r in map(json.loads, local.read_text().splitlines())}
        for url in a.show:
            r = by_url.get(url)
            print(f"## {url}")
            print(r["title"] if r else "")
            print(r["abstract"] if r else "(no abstract stored)")
            print()
        return
    scan = yaml.safe_load((ROOT / "spec.yaml").read_text())["scan"]
    end = date.fromisoformat(a.date)
    start = end - timedelta(days=scan["window_days"])
    out = ROOT / "candidates" / "feeds" / f"feeds_{end.isoformat()}.jsonl"
    old_rows = [json.loads(x) for x in out.read_text().splitlines()] if out.exists() else []
    old_abs = (
        {r["url"]: r["abstract"] for r in map(json.loads, local.read_text().splitlines())}
        if local.exists()
        else {}
    )
    rows = []
    for name, fn in (("arxiv", arxiv), ("huggingface", huggingface), ("zenodo", zenodo)):
        try:
            got = fn(scan["feeds"][name], start, end)
        except (requests.RequestException, ET.ParseError) as e:  # report, do not hide
            kept = [
                dict(r, abstract=old_abs.get(r["url"], "")) for r in old_rows if r["source"] == name
            ]
            print(f"{name}: FAILED ({type(e).__name__}); kept {len(kept)} rows from the last run")
            rows += kept
            continue
        print(f"{name}: {len(got)} items in {start} .. {end}")
        rows += got
    local.parent.mkdir(parents=True, exist_ok=True)
    local.write_text(
        "".join(
            json.dumps({"url": r["url"], "title": r["title"], "abstract": r["abstract"]}) + "\n"
            for r in rows
            if r.get("abstract")
        )
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "".join(json.dumps({k: v for k, v in r.items() if k != "abstract"}) + "\n" for r in rows)
    )
    print("wrote", out.relative_to(ROOT), len(rows), "rows; abstracts in", local.relative_to(ROOT))


if __name__ == "__main__":
    main()
