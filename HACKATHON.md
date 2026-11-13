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

## Questions for the organisers at kickoff

1. Is a disclosed, pre-built data and evaluation harness allowed?
2. Can one project be tagged for two tracks?
3. Is the Research API in scope, and what are the credit or rate limits?
4. Demo length, screen setup, and submission format?

## What is built on the day

Everything below is new on Saturday. The harness, data, baselines, model rows,
spec, schema, evaluation set and the rough judge prototype are prior work and are
disclosed in `README.md` and in the demo.

| Hour | Build |
|------|-------|
| 0:00 to 0:30 | Kickoff, confirm rules, recruit, assign roles |
| 0:30 to 1:30 | `/scan`: You.com search with recency and domain filters over arXiv, Hugging Face, GitHub and indexed LinkedIn snippets; write to the evidence ledger; dedupe by primary URL |
| 1:30 to 2:30 | `/judge` on You.com: cited claim extraction through the research tool, evidence-strength critic, scorecard JSON; re-run the 11-item evaluation and show agreement |
| 2:30 to 3:30 | `/run-candidate`: scorecard to harness config; a few windows live, full results precomputed; write the claimed-vs-measured receipt |
| 3:30 to 4:30 | Dashboard: leaderboard, scorecards with clickable citations, receipt cards, a "judge this URL" button |
| 4:30 to 5:30 | End to end on two fresh scan hits; freeze; rehearse |
| 5:30 to 6:00 | Buffer; README; backup video ready |

With teammates:

- A: `/scan` and `/judge` (skills, prompts, You.com integration)
- B: harness, `/run-candidate`, model rows
- C: dashboard
- D: evaluation of the judge, pitch, video, fallbacks

## Demo (3 minutes)

1. 0:00 to 0:20. A LinkedIn post claims that, given the same weather, a zero-shot
   model is barely better than a plain regression. Does that hold for a US grid,
   a week ahead?
2. 0:20 to 1:00. `/judge <url>`: You.com finds the primary sources; the scorecard
   shows pre-registered yes, baseline had the same inputs yes, horizon day-ahead vs.
   our 168 hours.
3. 1:00 to 2:00. `/run-candidate`: the model and the regression on JC and DOM, both
   weather regimes; a few windows live, the rest from the precomputed run.
4. 2:00 to 2:40. Dashboard receipt: claimed vs. measured ratio with its interval,
   and how much forecast weather costs each model.
5. 2:40 to 3:00. The judge's agreement on the 11 hand-labelled items; one rejected
   item and one "no primary source found" item; the search provider is swappable.

Say on stage: PJM load is public data that the models may have seen in training,
so backtest results carry a leakage caveat.

## Fallbacks

- Slow inference: run a few windows live, show the full run from cache.
- Weak live search: cached You.com responses in the ledger; the 11-item set.
- Network down: weights and data are local; backup video.
- Generated code: never executed in the main path; only registered adapters run.

## Guardrails

- LinkedIn: search-indexed snippets and URLs only. No login, no crawling.
- The judge reports a missing primary source; it never invents one.
- Non-commercial model weights are flagged on the leaderboard.
