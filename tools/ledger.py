"""Evidence ledger: every page a skill used, one JSON line each.

    uv run --project core python tools/ledger.py add --provider claude --candidate item-02 \
        --url https://... --title "..." --published 2026-11-12 --note "short paraphrase"
    uv run --project core python tools/ledger.py show --provider claude --candidate item-02

Stores URLs and short paraphrases only (CLAUDE.md rule 9). LinkedIn is refused (rule 10).
A note is at most 400 characters. A page with more to record gets several rows: call
`add` again with the same URL and a different note. `--published` is the date the page
was first published (YYYY-MM-DD), or `unknown`. A search that found nothing is recorded
with `--url` set to the search engine's address and the query and outcome in the note.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
MAX_NOTE = 400


def path(provider: str, candidate: str) -> Path:
    return ROOT / "evidence" / provider / f"{candidate}.jsonl"


def add(a: argparse.Namespace) -> None:
    host = (urlparse(a.url).hostname or "").lower()
    if not host:
        sys.exit("not a URL")
    if host == "linkedin.com" or host.endswith(".linkedin.com"):
        sys.exit("linkedin.com is not a source (CLAUDE.md rule 10)")
    if len(a.note) > MAX_NOTE:
        sys.exit(f"note is longer than {MAX_NOTE} characters: paraphrase, do not copy")
    row = {
        "evidence_id": hashlib.sha256(a.url.encode()).hexdigest()[:12],
        "url": a.url,
        "title": a.title,
        "published_at": a.published,
        "note": a.note,
        "provider": a.provider,
        "retrieved_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    p = path(a.provider, a.candidate)
    p.parent.mkdir(parents=True, exist_ok=True)
    old = [json.loads(line) for line in p.read_text().splitlines()] if p.exists() else []
    if any(r["url"] == a.url and r["note"] == a.note for r in old):
        print("already in ledger:", row["evidence_id"])
        return
    with p.open("a") as f:
        f.write(json.dumps(row) + "\n")
    print("added", row["evidence_id"])


def show(a: argparse.Namespace) -> None:
    p = path(a.provider, a.candidate)
    print(p.read_text() if p.exists() else "no ledger yet")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("add", "show"):
        sp = sub.add_parser(name)
        sp.add_argument("--provider", required=True, choices=["claude", "youcom", "manual"])
        sp.add_argument("--candidate", required=True)
        if name == "add":
            sp.add_argument("--url", required=True)
            sp.add_argument("--title", default="")
            sp.add_argument("--published", default="unknown")
            sp.add_argument("--note", default="")
    a = ap.parse_args()
    {"add": add, "show": show}[a.cmd](a)


if __name__ == "__main__":
    main()
