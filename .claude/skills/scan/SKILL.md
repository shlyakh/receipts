---
name: scan
description: Find forecasting claims published in the search window and write them as candidates. Use for "/scan" or "find new forecasting claims".
---

# /scan [provider]

Provider is `claude` unless given (see `.claude/skills/providers.md`).

1. Read `spec.yaml`: `problem`, `relevance`, `scan`. The window is the last
   `scan.window_days` days; compute the start date and use it in every query.
2. Run each query in `scan.queries` once per domain group in `scan.domains`, using the
   provider's `search`. Do not search or open `linkedin.com`.
3. For each hit, append one ledger row:
   `uv run --project core python tools/ledger.py add --provider <p> --candidate scan-<date> --url <url> --title <title> --published <date or unknown> --note <one-line paraphrase>`
4. Keep a hit as a candidate only if it is (a) published inside the window, (b) about
   forecasting a time series, and (c) points at a primary source: a model card, a
   repository, a paper or a data record. Drop news rewrites when the primary source is
   also in the hits.
5. Deduplicate by primary URL (strip query strings and trailing slashes; a GitHub
   repository and its Hugging Face card are one candidate).
6. Write `candidates/<provider>/scan_<YYYY-MM-DD>.jsonl`, one object per candidate:
   `candidate_id` (slug), `title`, `primary_url`, `other_urls`, `published_at`,
   `candidate_type` (enum in `schemas/scorecard.schema.json`), `claim` (one paraphrased
   sentence), `why_relevant`, `query` that found it.
7. Report: queries run, hits, candidates kept, and the five most relevant to the spec.
   Say what was dropped and why. Do not judge the candidates here.
