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
| 8 | Baseline to beat: a lag regression with weather, adapted from the GB demand study (per-hour fits, 7-day lag, calendar, weather terms); all models get identical weather. Vanilla + recency is a second baseline | The claim under test is that zero-shot models roughly tie this kind of regression given the same weather |
| 11 | Statistics follow the GB study: per-window MAE, error ratios, whole-week bootstrap with a fixed seed, pre-written result sentences | Makes the receipt comparable to the claim |
| 9 | Prior-work line: bring infrastructure only, disclosed; build the You.com agent on Saturday | Honest and defensible; confirm the rule at kickoff |
| 10 | Track: Receipts (ask at kickoff whether Receipts + The Analyst is allowed) | Verification by experiment is the distinctive part |

## Settled in the plan review, Thu Nov 12 (evening)

| # | Decision | Why |
|---|----------|-----|
| 12 | The receipt is a transfer test, not a replication: "does this claim carry over to my problem?". Verdicts: `transfers / partially / does_not_transfer / untestable`. A per-lead-day ratio (day 1 to 7) is a pre-registered secondary | The GB claim is day-ahead with a 2-day lag and 1,035 origins; ours is week-ahead, 7-day lag only, 52 origins |
| 13 | Tonight's order: draft the protocol, gate on 4 pre-window origins, tag, score the 52 origins once. Row-ordering checks are gates, not conditions on the scored result | The scored windows are never run by code that is later changed |
| 14 | Prior work is assumed allowed; Friday is open for experimenting with Claude and other LLMs. Still confirm at kickoff | Yuri's call |
| 15 | Primary comparison: Chronos-2 with temperature vs. the lag regression with temperature, forecast regime, per zone. Bar 10%, verdict read from the whole 90% interval, four pre-written outcome sentences. Everything else is secondary. Illustration: https://claude.ai/artifact/TSpY7YUQmdC9Yf7BetQGgC | Many ratios invite picking one after the fact; the forecast regime is the one a practitioner faces |
| 16 | Friday's acceptance bar is Chronos-2 only. Target 2 to 3 models (TimesFM 2.5 and Timestral next, the GB study's three), hard stop at 12:00. Model ids are verified Thursday overnight | The headline needs one model; the afternoon belongs to the judge and readiness |
| 17 | `protocol-v1` uses temperature only, as a deliberate choice. Wind, solar and dew point are fetched and hashed but unused. The baseline is always named "temperature-only regression" | PJM zonal load is mostly temperature-driven; three variables triple the alignment checks |
| 18 | The idealised cutoff stays (load visible up to the cutoff) with a named caveat that it favours models using recent context. A Chronos-2 row with a 48-hour data gap is a pre-registered secondary | EIA load lags 1 to 2 days; the regression's only load input is a week old, the model's is not |
| 19 | Yuri labels the 11 evaluation items blind; that is the ground truth. A claim with no primary source is capped at `PARTIAL` unless the candidate is a runnable model release. Agreement is reported as a regression test with misses explained | Labels proposed by Claude and judged by Claude measure consistency, not correctness |
| 20 | Saturday build order: `/judge` on You.com, `/run-candidate`, a static receipt page, rehearsal, then `/scan`, then dashboard extras. First cuts: the "judge this URL" button and a full `/scan` | The demo path must exist before anything is widened |
| 21 | LinkedIn is out of the pipeline unless Yuri finds a better route by Saturday. A stored LinkedIn URL is an identifier only. The demo input is Zenodo record 24161799 | No compliant way to read posts; the record now holds the weather results |
| 22 | Model weights are pinned to a Hugging Face revision. Leakage is reported per model as "N of 52 scored weeks postdate the weights" | Turns a blanket caveat into a checkable statement |
| 23 | The dashboard is built before Saturday as a static web page (HTML, D3, data exported from `results/`), not Streamlit. It opens with the story: what load forecasting is, PJM among the US grid operators, the two zones, then the receipt, the leaderboard, the agents and the path to a product (Yuri, Nov 13) | Yuri wants to see and shape it early; a static page needs no server on stage and can be shared as a link. It is disclosed as prior work |
| 24 | `/scan`, `/judge` and `/run-candidate` are built before Saturday on Claude's own search and fetch, then run again on You.com and compared on the same inputs. Outputs are kept per provider. Search window: the last 120 days (Yuri, Nov 13: "3 to 4 months") | A working agent exists before the hackathon; the You.com comparison becomes a result, not a dependency |
| 25 | LinkedIn stays excluded as a source (decision 21) while a separate investigation looks at legitimate ways to follow forecasting news from LinkedIn, or to replace it with X/Twitter or another feed. Report in `notes/social_sources.md` (Yuri, Nov 13) | Most of the 11 evaluation items were found there; the pipeline needs a feed it is allowed to read |
| 26 | Baselines are chosen by a recorded search for the field's standards (`BASELINES.md`), not from recent publications alone. Tao's Vanilla Benchmark was added in two forms as secondary rows under `protocol-v1.1` (Yuri, Nov 13). A future protocol should name its primary baseline only after that search | The frozen baseline turned out weaker than the field's standard; against the standard, Chronos-2's lead largely disappears |
| 27 | Future plan, not started: test newly released models on data they cannot have seen, by (a) a prospective panel across zones and operators and (b) semi-synthetic load from two simulator families with real residuals, validated first on 2023 to 2024 where real scores exist (`notes/unseen_data_for_new_models.md`) (Yuri, Nov 13) | Models whose weights fall inside the scored window cannot be tested fairly today |

Also fixed: `spec.yaml` names the lag regression with temperature as the baseline
to beat; the LightGBM row uses exactly the lag regression's input columns.

## Open questions

- Confirm inside the Zenodo 24161799 zip (`weather_study/RESULTS.md`) the GB
  weather-study ratios quoted in the post. The weather gains (34 / 32 / 23 / 6%)
  appear in the record's description. Friday.
- How wide is a 90% interval on the ratio with 52 weekly blocks? If it is wider
  than the 10% bar on both sides, most outcomes will read "inconclusive".
- Is the prior-work rule at this event compatible with decisions 9 and 14? Ask at
  kickoff.
- Which foundation models are fast enough on the laptop for a full 52-window run?
  Benchmark one window each on Friday morning.
- Whether to tell the GB study's author before Saturday. Yuri's call.
- RESEARCH TASK, deferred (Yuri, Nov 13): how to evaluate the newest foundation
  models fairly when their weights were fixed inside the scored window. Checked on
  Nov 13 from each weights file's commit date: Chronos-2 (2025-10-30) and TimesFM 2.5
  (2025-10-01) predate all 52 scored weeks; TimesFM-3 (2026-08-24) predates only 11.
  Candidate answers: a rolling forward window scored as new weeks arrive; the
  post-weights subset as the only reported number; a live check like the GB study's
  part 2.

## Out of scope for the hackathon

- Medium- and long-term horizons.
- Fine-tuning any model.
- Running arbitrary paper code that is not in the runnable class.
- LinkedIn as a source (decision 21): no login, no crawling, no fetching post pages.
- Wind, solar and dew point as model inputs (decision 17): a later protocol version.
- A true day-ahead replication with daily origins (decision 12).
