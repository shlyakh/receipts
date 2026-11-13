---
name: judge
description: Judge one forecasting candidate against spec.yaml and write a scorecard with cited sources. Use for "/judge <item id or URL>".
---

# /judge <item id | candidate id | URL> [provider]

Provider is `claude` unless given (see `.claude/skills/providers.md`).

1. Read `spec.yaml` and `schemas/scorecard.schema.json`. Resolve the input: an id from
   `eval/items.yaml` (use only `title`, `claim`, `discovered_via`, `primary_sources`;
   never read `label_proposed`, `label_yuri`, `reason`, `verified` or `unverified`), an id from a
   `candidates/` file, or a URL.
2. Gather evidence with the provider's `search` and `fetch`. Look for the primary
   source first: model card, repository, paper, data record. For each page used, add a
   ledger row with `tools/ledger.py add` (URL, title, published date, a short
   paraphrase of what it says). Never open `linkedin.com`.
   `uv run --project core python tools/ledger.py add --provider <p> --candidate <id> --url <url> --title "<title>" --published <YYYY-MM-DD|unknown> --note "<at most 400 characters>"`
   A page with more to record gets several rows (same URL, different note). Record a
   search that found nothing too. The 120-day window is for `/scan`, not for sources
   read here. Budget: about 8 searches and 10 fetches.
3. Write the scorecard from the ledger only.
   - Every claim has `citation_idx` pointing at a primary source, or `null`.
   - If no primary source can be found, say so in `label_reason`, leave
     `primary_sources` empty, and cap the label at `PARTIAL` (the schema enforces it)
     unless the candidate is itself a runnable model release. Never invent a source.
   - `relevance` scores follow the 0 to 3 scales in `spec.yaml`.
   - `primary_sources` are the candidate's own record, repository, paper, plan and
     results files. The model card of the central model may be added for its licence
     and weights date.
   - `discovered_via.provider` is who found the lead (`manual` for `eval/items.yaml`);
     `retrieved_at` is the time of this run.
   - One claim per number, with `ci90` when the source gives an interval. Use
     `baseline_same_inputs: partly` when some inputs matched and some did not.
   - `evidence_strength`, `independent_replication`, the central model of a study and
     ACCEPT_RUN for a study follow `judging` in `spec.yaml`. Put the reasoning and
     anything unverified in `checks.notes`.
   - `checks.training_overlap_risk`: follow `judging.training_overlap_risk` in
     `spec.yaml` (the weights file's commit date against `scored_window`).
   - `runnable_class` and `implementation_hint` come from `runnable_models` in
     `spec.yaml`: the script and the weights repository.
   - `receipt` is `null`; `/run-candidate` fills it.
4. Save to `scorecards/<provider>/<candidate_id>.json` and validate:
   `uv run --project core python tools/validate_scorecard.py scorecards/<provider>/<candidate_id>.json`
   Fix and re-validate until it passes.
5. Report the label, the reason in two sentences, the sources cited, how the
   candidate's setup differs from ours (target, horizon, inputs), and anything that
   could not be verified.
