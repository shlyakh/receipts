# Receipts for Forecasting Papers

An agent that reads newly published forecasting methods, judges whether they apply
to a specific problem with every claim cited, and runs the runnable ones on our own
benchmark to report claimed vs. measured.

Benchmark: PJM hourly electricity load, zones JC and DOM, week-ahead (168 hours).

## Status

As of Fri Nov 13, 2026:

- **Data:** EIA load for JC and DOM and Open-Meteo weather, hashed in `fetch_manifest.json`.
- **Protocol:** `protocol.yaml`, frozen at git tag `protocol-v1` (commit `912a902`) after
  all gate checks passed. Not edited since.
- **Leaderboard** (`results/README.md`), each row scored once on 48 of 52 weeks: four
  simple methods; Chronos-2 with and without temperature, and with a 48-hour data gap;
  TimesFM 2.5 with and without temperature; Timestral (labelled not out-of-sample).
- **Primary result:** Chronos-2 with temperature against the regression with
  temperature, forecast weather: DOM 0.730 (90% interval 0.665 to 0.805), JC 0.817
  (0.686 to 0.960).
- **Agent skills on Claude's own search** (`.claude/skills/`): `/scan`, `/judge`,
  `/run-candidate`, with an evidence ledger, a scorecard schema and a receipt tool.
  Outputs are kept per search provider in `candidates/`, `evidence/`, `scorecards/`.
- **Run capture:** `tools/run_skill.py` runs a skill headless and records the run in
  `runs/`. A local Langfuse instance is set up for tracing (not yet connected).
- **Dashboard:** `dashboard/index.html` (tabs) and `dashboard/story.html` (a scrolling
  story), both static pages built from `results/` by `dashboard/build_data.py`.
- **Not yet:** Yuri's blind labels and the judge agreement table; the You.com provider.

Run from the repo root:

```
uv run --project core python fetch.py verify
uv run --project core pytest tests -q
uv run --project core python tools/run_skill.py scan claude
uv run --project core python tools/run_skill.py judge claude <candidate id>
uv run --project core python dashboard/build_data.py
```

## Prior work disclosure

This project is being entered in the Ground Truth hackathon (New York, Nov 14, 2026).
Everything listed under Status is built before the event and is not hackathon work:

- data pull, weather pull, frozen backtest protocol, evaluation harness
- baselines and foundation-model leaderboard rows
- problem spec, scorecard schema, 11-item evaluation set
- the three agent skills running on Claude's own web search and public listings
- the dashboard and story pages

Built on the day: the You.com search provider for the same skills, the comparison of
the two providers on the same inputs, and whatever the day's scan finds and runs.
Commit timestamps and the `protocol-v1` tag show the boundary.

## Documents

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Rules for anyone (or any agent) working in this repo |
| `DECISIONS.md` | Fixed design choices and open questions |
| `TONIGHT.md` | Thursday brief: data, protocol, baselines |
| `FRIDAY.md` | Friday brief: model rows, spec, judge prototype |
| `HACKATHON.md` | Saturday plan, pitch, demo script |
| `REFERENCE.md` | Endpoints, formulas, schemas, unverified items |
| `notes/moran.md` | Notes on the GB demand study whose design we mirror |
| `eval/items.yaml` | 11 candidates for testing the judge (`eval/label_sheet.md` for blind labelling) |
| `spec.yaml` | The problem the judge scores against, and the scan's configuration |
| `notes/` | Reading notes: the GB study, FoundationForecast, feeds, telemetry |

## Acknowledgements

The backtest discipline follows Andy Moran's GB demand studies
(`AndyMoran/gb-foundation-model-tests`). The skills approach follows
`dgilford/ai-science-toolkit`. Foundation models are run through
`TimeCopilot/foundationforecast`.
