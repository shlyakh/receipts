# Receipts for Forecasting Papers

An agent that reads newly published forecasting methods, judges whether they apply
to a specific problem with every claim cited, and runs the runnable ones on our own
benchmark to report claimed vs. measured.

Benchmark: PJM hourly electricity load, zones JC and DOM, week-ahead (168 hours).

## Status

Planning and handoff documents only. No code yet.

## Prior work disclosure

This project is being entered in the Ground Truth hackathon (New York, Nov 14, 2026).
The following is built before the event and is not hackathon work:

- data pull, weather pull, frozen backtest protocol
- evaluation harness, baselines, foundation-model leaderboard rows
- problem spec, scorecard schema, 11-item labelled evaluation set
- a rough prototype of the judge used to settle the schema

Built on the day: the You.com-powered agent (`/scan`, `/judge` with cited research,
`/run-candidate`, the dashboard). Commit timestamps and the `protocol-v1` tag show
the boundary.

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
| `eval/items.yaml` | 11 labelled candidates for testing the judge |

## Acknowledgements

The backtest discipline follows Andy Moran's GB demand studies
(`AndyMoran/gb-foundation-model-tests`). The skills approach follows
`dgilford/ai-science-toolkit`. Foundation models are run through
`TimeCopilot/foundationforecast`.
