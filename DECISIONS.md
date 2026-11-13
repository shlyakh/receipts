# Decisions (fixed unless Yuri changes them)

Settled Thu Nov 12, 2026.

| # | Decision | Why |
|---|----------|-----|
| 1 | Goal: build the seed of a tool Yuri keeps developing; shape the demo to land with judges | The reusable pipeline is worth more than the prize |
| 2 | Pipeline: monitor, judge relevance (cited), suggest implementation, run it | Stages 1 to 3 are must-have; "run it" only for a constrained runnable class |
| 3 | Benchmark: PJM hourly load, zones JC and DOM, 168-hour horizon | Real problem, public data, backtests fast enough to run live |
| 4 | Runtime: Claude Code skills first (`/scan`, `/judge`, `/run-candidate`); standalone app maybe later | Manual runs now, no always-on agent |
| 5 | Search is swappable: Claude web search on Friday, You.com MCP on Saturday, others later | Skills read from an evidence ledger, not from a provider |
| 6 | Model layer: FoundationForecast for foundation models, plus one direct Chronos-2 adapter as fallback | Saves time; young library, so keep a fallback |
| 7 | Harness owns data, weather, cutoffs, metrics, and non-foundation baselines | Needed for the forecast-weather regime and for comparability |
| 8 | Baseline to beat: plain weather regression; all models get identical weather | A GB demand study reports zero-shot models roughly tie a weather regression given the same weather |
| 9 | Prior-work line: bring infrastructure only, disclosed; build the You.com agent on Saturday | Honest and defensible; confirm the rule at kickoff |
| 10 | Track: Receipts (ask at kickoff whether Receipts + The Analyst is allowed) | Verification by experiment is the distinctive part |

## Open questions

- Does the GB study's Zenodo record (10.5281/zenodo.24161799) specify a regression we
  should mirror exactly? Yuri to read and paste into `notes/moran.md`.
- Is the prior-work rule at this event compatible with decision 9? Ask at kickoff.
- Which foundation models are fast enough on the laptop for a full 52-window run?
  Benchmark one window each on Friday morning.

## Out of scope for the hackathon

- Medium- and long-term horizons.
- Fine-tuning any model.
- Running arbitrary paper code that is not in the runnable class.
- Reading LinkedIn directly (search-indexed snippets only; no login, no crawling).
