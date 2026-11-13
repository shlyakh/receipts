# Saturday Nov 14: hackathon plan

Event: "Ground Truth: The Live Agents Hackathon, powered by You.com", New York.
https://luma.com/live-agents-hack-nyc

- One day, about 6 hours of building, live demos to judges at the end.
- Required tooling: You.com API (Search, Contents, Research, hosted MCP server).
- Teams of up to 4, or solo; team matching at kickoff.
- Tracks: Live Wire (real-time agents), The Analyst (cited deep research),
  Receipts (checking claims and sources), Best Content (post about the build).
- Published prizes: first place overall and Best Content. No scoring criteria are
  published.

## Entry

Track: Receipts. Ask whether Receipts + The Analyst can both be tagged.

Pitch: "Every week new forecasting models claim to be the best. This agent reads
the claims as they appear, checks whether they even apply to my grid-load problem
with every statement cited, and then runs the runnable ones on my own PJM data.
I get receipts, not hype."

The receipt is a transfer test: it says whether a claim carries over to my problem,
not whether the original claim is true (decision 12).

## Questions for the organisers at kickoff

1. Is a disclosed, pre-built data and evaluation harness allowed? (Assumed yes,
   decision 14. If no: bring the cached results as a dataset and show the harness
   in the repo history only.)
2. Can one project be tagged for two tracks?
3. Is the Research API in scope, and what are the credit or rate limits?
4. Demo length, screen setup, and submission format?

## What is built on the day

Everything below is new on Saturday. The harness, data, baselines, model rows,
spec, schema, evaluation set and the rough judge prototype are prior work and are
disclosed in `README.md` and in the demo.

Build the demo path first, then widen it (decision 20).

| Hour | Build |
|------|-------|
| 0:00 to 0:30 | Kickoff, confirm rules, recruit, assign roles |
| 0:30 to 1:30 | `/judge` on You.com, written fresh: cited claim extraction through the research tool, scorecard JSON; run it on item-02 (Zenodo record 24161799) |
| 1:30 to 2:30 | `/run-candidate`: scorecard to harness config; a few windows live, full results precomputed; write the receipt (claimed, measured ratio with interval, verdict, horizon mismatch, weeks after weights) |
| 2:30 to 3:15 | Static receipt page: one HTML file generated from the leaderboard and scorecards, with clickable citations |
| 3:15 to 3:45 | First end-to-end rehearsal of the 3-minute demo |
| 3:45 to 4:30 | `/scan`: You.com search with recency and domain filters over arXiv, Hugging Face, GitHub and Zenodo; write to the evidence ledger; dedupe by primary URL. A thin version is one query and a dedupe |
| 4:30 to 5:00 | Re-run the evaluation set through `/judge`; agreement table with misses explained; evidence-strength critic if time allows |
| 5:00 to 5:30 | End to end on one fresh scan hit; freeze; rehearse |
| 5:30 to 6:00 | Buffer; README; backup video ready |

Cut first, in this order: the "judge this URL" button, the leaderboard view, the
evidence-strength critic, a full `/scan`. Run `/judge` in the terminal in front of
the judges: it shows the agent working.

With teammates:

- A: `/scan` and `/judge` (skills, prompts, You.com integration)
- B: harness, `/run-candidate`, model rows
- C: dashboard
- D: evaluation of the judge, pitch, video, fallbacks

## Demo (3 minutes)

1. 0:00 to 0:20. A pre-registered study published this week claims that, given the
   same weather, a zero-shot model roughly ties a plain regression on GB demand, a
   day ahead. Does that transfer to a US grid, a week ahead?
2. 0:20 to 1:00. `/judge <Zenodo URL>`: You.com finds and quotes the primary
   sources; the scorecard shows pre-registered yes, baseline had the same inputs
   yes, horizon day-ahead vs. our 168 hours.
3. 1:00 to 2:00. `/run-candidate`: Chronos-2 and the temperature-only regression on
   JC and DOM, forecast weather; a few windows live, the rest from the precomputed
   run.
4. 2:00 to 2:40. Receipt page: the measured ratio with its interval against the
   10% bar, the pre-written outcome sentence, and the per-lead-day curve. Secondary:
   how much forecast weather costs each forecaster.
5. 2:40 to 3:00. The judge on the hand-labelled evaluation set as a regression
   test: N matched, one miss explained, one "no primary source found" item; the
   search provider is swappable.

Say on stage, per model and only if Friday's check confirms it: "all 52 scored
weeks postdate these weights, so the model cannot have trained on them". For a
model released during the window: "N of 52 weeks postdate the weights". For every
model: earlier years of the same public series may be in training.

Also say: the protocol, the primary comparison and the outcome sentences were
frozen at a pushed git tag before the scored run, and the scored run happened once.

## Fallbacks

- Slow inference: run a few windows live, show the full run from cache.
- Weak live search: cached You.com responses in the ledger; the evaluation set.
- Zenodo record not found by You.com search: pass its URL to the contents tool
  directly (checked in Friday's smoke test).
- Network down: weights and data are local; backup video.
- Generated code: never executed in the main path; only registered adapters run.

## Guardrails

- LinkedIn is not a source (decision 21): no login, no crawling, no fetching, no
  snippets as evidence. Revisit only if Yuri finds a better route.
- The judge reports a missing primary source; it never invents one.
- Non-commercial model weights are flagged on the leaderboard.
