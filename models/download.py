"""Download model weights at a pinned revision and record the pin.

    uv run --project models python models/download.py amazon/chronos-2 <full commit sha>

Writes models/pins.json: repo id -> revision, and the commit date of each weights file.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from huggingface_hub import HfApi, snapshot_download

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "models_cache"
PINS = ROOT / "models" / "pins.json"
WEIGHT_SUFFIXES = (".safetensors", ".bin", ".pt", ".ckpt")


def main() -> None:
    repo_id, revision = sys.argv[1], sys.argv[2]
    load_dotenv(ROOT / ".env")
    token = os.environ.get("HF_TOKEN") or None
    api = HfApi(token=token)
    files = api.list_repo_tree(repo_id, revision=revision, expand=True, recursive=True)
    weights = {
        f.path: f.last_commit.date.isoformat()
        for f in files
        if f.path.endswith(WEIGHT_SUFFIXES) and getattr(f, "last_commit", None)
    }
    path = snapshot_download(repo_id, revision=revision, cache_dir=CACHE, token=token)
    pins = json.loads(PINS.read_text()) if PINS.exists() else {}
    pins[repo_id] = {
        "revision": revision,
        "weights_files": weights,
        "weights_date": max(weights.values()) if weights else None,
    }
    PINS.write_text(json.dumps(pins, indent=1, sort_keys=True) + "\n")
    print(repo_id, revision[:10], "->", path)
    print("weights date:", pins[repo_id]["weights_date"])


if __name__ == "__main__":
    main()
