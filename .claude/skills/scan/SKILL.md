---
name: scan
description: Find forecasting claims published in the search window and write them as candidates. Use for "/scan" or "find new forecasting claims".
---

# /scan [provider]

Provider is `claude` unless given (see `.claude/skills/providers.md`).

1. Read `spec.yaml`: `problem`, `scan`. The window is the last `scan.window_days`
   days; compute the start date.
2. Run each query in `scan.queries` once per domain group in `scan.domains`, using the
   provider's `search` (first page of results only). Pass the start date if the
   provider's search takes one; Claude's web search does not, so expect out-of-window
   hits. Never search or open `linkedin.com`; for the open-web group, block it.
3. Add one ledger row per distinct URL (collapse arXiv abs/pdf/html/versioned links to
   the abs URL):
   `uv run --project core python tools/ledger.py add --provider <p> --candidate scan-<YYYY-MM-DD> --url <url> --title "<short title>" --published <YYYY-MM-DD|YYYY-MM|unknown> --note "<KEPT|FOLDED|DROPPED: reason. One-line paraphrase. Query: ...>"`
   This is the scan's own ledger. `/judge` gathers its own evidence per candidate.
4. Establish each promising hit's publication date. Use the date in the search result
   when it is explicit; otherwise `fetch` the page (budget: about 15 fetches, spent on
   the hits closest to the spec). "Published" is the first public version of the thing
   the claim is about: the first arXiv version for a paper, the release date for
   weights or code. An approximate age is `unknown`.
5. Keep a hit as a candidate only if it is (a) dated inside the window, (b) about
   forecasting a time series, and (c) points at a primary source: a paper, a data or
   code record, a repository, a model card, or the publisher's own announcement. Drop
   news rewrites and roundups; if a roundup names a release with no primary source in
   the hits, list it under "worth a manual look".
6. Deduplicate: a paper, its repository, its model card, its data record and mirrors
   are one candidate. The primary URL is the paper or record; the rest go in
   `other_urls`.
7. Write `candidates/<provider>/scan_<YYYY-MM-DD>.jsonl`, one object per candidate:
   `candidate_id` (slug), `title`, `primary_url`, `other_urls` (list), `published_at`
   (YYYY-MM-DD), `candidate_type` (enum in `schemas/scorecard.schema.json`), `claim`
   (one paraphrased sentence), `why_relevant` (one sentence against `problem`),
   `query` (the query text that found it).
8. Report: queries run, distinct hits, candidates kept, the five closest to the spec's
   problem (a ranking by fit, not a judgement), what was dropped and why, anything
   worth a manual look, and every date or claim not confirmed by a fetch.
