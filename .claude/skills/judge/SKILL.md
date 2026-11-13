---
name: judge
description: Judge one forecasting candidate against spec.yaml and write a scorecard with cited sources. Use for "/judge <item id or URL>".
---

# /judge <item id | candidate id | URL> [provider]

Provider is `claude` unless given (see `.claude/skills/providers.md`).

1. Read `spec.yaml` and `schemas/scorecard.schema.json`. Resolve the input: an id from
   `eval/items.yaml` (use only `title`, `claim`, `discovered_via`, `primary_sources`;
   never read `label_proposed`, `label_yuri` or `reason`), an id from a
   `candidates/` file, or a URL.
2. Gather evidence with the provider's `search` and `fetch`. Look for the primary
   source first: model card, repository, paper, data record. For each page used, add a
   ledger row with `tools/ledger.py add` (URL, title, published date, a short
   paraphrase of what it says). Never open `linkedin.com`.
3. Write the scorecard from the ledger only.
   - Every claim has `citation_idx` pointing at a primary source, or `null`.
   - If no primary source can be found, say so in `label_reason`, leave
     `primary_sources` empty, and cap the label at `PARTIAL` (the schema enforces it)
     unless the candidate is itself a runnable model release. Never invent a source.
   - `relevance` scores follow the 0 to 3 scales in `spec.yaml`.
   - `checks.training_overlap_risk`: compare the weights' publication date with our
     scored window (2025-11-10 to 2026-11-02).
   - `runnable_class` follows `spec.yaml`; `implementation_hint` names the wrapper or
     adapter and the weights repository.
   - `receipt` is `null`; `/run-candidate` fills it.
4. Save to `scorecards/<provider>/<candidate_id>.json` and validate:
   `uv run --project core python tools/validate_scorecard.py scorecards/<provider>/<candidate_id>.json`
   Fix and re-validate until it passes.
5. Report the label, the reason in two sentences, the sources cited, and anything
   that could not be verified.
