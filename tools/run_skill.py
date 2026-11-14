"""Run one skill headless and keep the full record of the run.

    uv run --project core python tools/run_skill.py scan claude
    uv run --project core python tools/run_skill.py judge claude item-02
    uv run --project core python tools/run_skill.py scan claude --note "write to ..._run3"

Starts `claude -p "/<skill> <args> <provider>"` in this repository and writes
  runs/<run_id>.jsonl      every message, tool call, search and fetch (git-ignored: it
                           holds page text)
  runs/<run_id>.meta.json  provider, skill, arguments, git commit, session id, turns,
                           tokens, estimated cost, duration (committed)
The provider decides which search tools the run may use. `youcom` is wired on Saturday.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMMON = ["Read", "Write", "Edit", "Glob", "Grep", "Skill", "Bash(uv run:*)"]
TOOLS = {"claude": ["WebSearch", "WebFetch"]}


def git(*a: str) -> str:
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def parse(stream: Path) -> tuple[dict, dict]:
    """The final result line and a count of tool calls, from a saved stream."""
    result, tools = {}, {}
    for line in stream.read_text().splitlines():
        try:
            m = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(m, dict):
            continue
        if m.get("type") == "result":
            result = m
        message = m.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        for block in content if isinstance(content, list) else []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                tools[block["name"]] = tools.get(block["name"], 0) + 1
    return result, tools


def run(
    skill: str, provider: str, args: list[str], note: str = "", model: str = "", timeout: int = 3600
) -> dict:
    """Run one skill headless, save the stream and the metadata, return the metadata
    (with the final message under "result")."""
    if provider not in TOOLS:
        sys.exit("the youcom provider is wired on Saturday (CLAUDE.md phase gate)")
    started = datetime.now(UTC)
    # The first argument and a random suffix keep runs started in the same second apart.
    what = "".join(c if c.isalnum() else "-" for c in (args[0] if args else "all"))[:40]
    run_id = f"{started:%Y%m%dT%H%M%S}_{skill}_{provider}_{what}_{secrets.token_hex(2)}"
    prompt = " ".join([f"/{skill}", *args, provider]) + (f"\n\n{note}" if note else "")
    cmd = [
        "claude",
        "-p",
        prompt,
        "--output-format",
        "stream-json",
        "--verbose",
        "--allowedTools",
        *COMMON,
        *TOOLS[provider],
    ]
    if model:
        cmd += ["--model", model]
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE")}
    stream = ROOT / "runs" / f"{run_id}.jsonl"
    stream.parent.mkdir(exist_ok=True)
    t0 = time.perf_counter()
    timed_out = False
    with stream.open("w") as f:
        try:
            code = subprocess.run(
                cmd,
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                stdout=f,
                stderr=subprocess.PIPE,
                env=env,
                timeout=timeout,
            ).returncode
        except subprocess.TimeoutExpired:
            code, timed_out = -1, True
    result, tools = parse(stream)
    dirty = "-dirty" if git("status", "--porcelain", "--untracked-files=no") else ""
    meta = {
        "run_id": run_id,
        "skill": skill,
        "provider": provider,
        "args": args,
        "note": note,
        "model_requested": model or None,
        "git_commit": git("rev-parse", "--short", "HEAD") + dirty,
        "started_at": started.isoformat(timespec="seconds"),
        "wall_seconds": round(time.perf_counter() - t0, 1),
        "exit_code": code,
        "timed_out": timed_out,
        "session_id": result.get("session_id"),
        "is_error": result.get("is_error"),
        "num_turns": result.get("num_turns"),
        "total_cost_usd": result.get("total_cost_usd"),  # the client's estimate
        "usage": result.get("usage"),
        "model_usage": result.get("modelUsage"),
        "tool_calls": tools,
    }
    (ROOT / "runs" / f"{run_id}.meta.json").write_text(json.dumps(meta, indent=1) + "\n")
    return {**meta, "result": result.get("result")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("skill", choices=["scan", "judge", "run-candidate"])
    ap.add_argument("provider", choices=["claude", "youcom"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--note", default="", help="extra instruction appended to the prompt")
    ap.add_argument("--model", default="", help="model for the run; default is the CLI's own")
    a = ap.parse_args()
    meta = run(a.skill, a.provider, a.args, a.note, a.model)
    print(json.dumps({k: meta[k] for k in ("run_id", "exit_code", "num_turns", "total_cost_usd")}))
    if meta["result"]:
        print(meta["result"])


if __name__ == "__main__":
    main()
