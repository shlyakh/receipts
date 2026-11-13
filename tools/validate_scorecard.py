"""Validate scorecards against schemas/scorecard.schema.json.

uv run --project core python tools/validate_scorecard.py scorecards/claude/item-02.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parent.parent


def errors(card: dict) -> list[str]:
    schema = json.loads((ROOT / "schemas" / "scorecard.schema.json").read_text())
    v = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    out = [f"{'/'.join(map(str, e.path)) or '(root)'}: {e.message}" for e in v.iter_errors(card)]
    n = len(card.get("primary_sources", []))
    for i, c in enumerate(card.get("claims", [])):
        idx = c.get("citation_idx")
        if idx is not None and idx >= n:
            out.append(f"claims/{i}: citation_idx {idx} points past the {n} primary sources")
    return out


def main() -> None:
    if not sys.argv[1:] or sys.argv[1] in ("-h", "--help"):
        sys.exit(__doc__)
    bad = 0
    for name in sys.argv[1:]:
        errs = errors(json.loads(Path(name).read_text()))
        print(name, "OK" if not errs else "INVALID")
        for e in errs:
            print("  -", e)
        bad += bool(errs)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
