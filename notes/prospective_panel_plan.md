# Prospective panel: plan for the Monday run

Written 2026-11-13. A plan only; nothing here is built. The panel is defined in the
`prospective_panel` block of `protocol-v2-draft.yaml` (decision 32).

## What has to happen each week

**Sunday night job (the forecast).** Must finish before Monday 00:00 America/New_York.

1. Fetch load for every panel zone up to the latest hour EIA has published. Record the
   last hour received per zone (the data gap; expect 1 to 2 days).
2. Fetch the temperature forecast for the coming 168 hours from the latest AIFS run
   that was issued before the job started, and ERA5 for the history. Record the run.
3. Hash the raw files into a manifest for that week.
4. Run every registered row once per zone. No retries with changed settings.
5. Write `results/panel/<monday>/forecasts.parquet` and `manifest.json`, commit and push.
   The push time is the evidence that the forecast preceded the week.

**Scoring job (any time after the week's load is complete, about 9 days later).**

6. Fetch the week's actual load, score the stored forecasts, append one row per model
   and zone to `results/panel/scores.parquet`, commit and push.
7. A week whose forecast was late, missing or incomplete is listed as dropped. It is
   never back-filled.

## What is new to build (none of it exists)

| Piece | Why the backtest code does not cover it |
|---|---|
| Live load fetch | `fetch.py` pulls a fixed historical range; the panel needs "everything up to now" and must tolerate the EIA lag |
| Live weather fetch | The backtest reads archived forecasts by lead day; the panel reads the forecast as issued now, from Open-Meteo's forecast endpoint with the model named |
| History with a data gap | Models get load that ends 1 to 2 days before the issue time. Chronos-2 has a tested 48-hour-gap mode; the regressions and LightGBM need the same treatment defined |
| Panel runner | One command that does steps 1 to 5 and refuses to overwrite an existing week |
| Panel scorer | Steps 6 and 7, with the same statistics code as the backtest |
| Checkpoint reader | Reads the primary ratio only at 13, 26 and 52 scored weeks |

Rough size: two to three days of work, most of it the live fetch and the data-gap rule.

## What must be decided first

1. **Which protocol the first counted week runs under.** The panel may only run rows
   registered in a tagged protocol. `protocol-v2` is not tagged: the weather points for
   AEP and AE, their data pull, the calendar row and the gate runs are still open.
2. **The data-gap rule.** How each model treats the 1 to 2 days of missing recent load.
   This is a definition, so it belongs in the protocol before the first counted week.
3. **Which AIFS run counts as "available".** Proposal: the latest run whose data
   Open-Meteo serves when the job starts, with the run time recorded. When each run
   becomes available on Open-Meteo is not verified.
4. **Where it runs** (next section).

## Where it could run

| Option | For | Against |
|---|---|---|
| Scheduled job on the laptop (launchd or cron) | Everything is already installed; free; fastest to set up | The laptop must be on and awake every Sunday night; a missed night is a dropped week; the only proof of timing is our own push |
| GitHub Actions, scheduled workflow | Free for a public repository; no machine of ours involved; GitHub records when the run happened and when the push landed, which is independent evidence of timing; secrets store for the EIA key | Schedules are in UTC and can start late or be skipped under load, so it should start hours early; the model weights must be cached or downloaded each run; a 4-core runner makes the slow rows slower |
| Claude scheduled agent (Cowork or a cloud routine) | Can check the output, write the weekly summary and raise problems in plain words | An agent should not be the thing that produces the forecast: the run must be a fixed script. Each run costs tokens. Whether it can hold the model environments and weights is not verified |
| Small cloud machine or container job on a schedule | Most reliable; the natural step if the project moves to the cloud anyway | A few dollars a month; the most setup; needs an account, secrets and monitoring |

**Recommendation.** GitHub Actions runs the fixed script and pushes the forecasts. The
laptop job is kept as a documented manual fallback. A Claude scheduled agent, if wanted,
only reads the result on Monday morning and reports. A cloud machine replaces GitHub
Actions later if scheduled runs prove unreliable or the rows outgrow the runner.

Proof of timing in every option: the pushed commit, plus the hash manifest. If stronger
proof is wanted, the weekly manifest hash can also be posted somewhere we do not
control (a public timestamping service); not needed to start.

## Proposal for Monday Nov 16, 2026

Monday is two days away and Saturday is the hackathon, so a counted week is not
realistic: `protocol-v2` will not be tagged and none of the pieces above exist.

- **Nov 16: no counted run.** If time allows on Sunday, a hand-run dry run on DOM and JC
  with the existing rows, saved under `results/panel_dryrun/` and labelled as not part
  of the panel. Its purpose is to learn the real timings: how late EIA load is on a
  Sunday night and which AIFS run is being served.
- **First counted week:** the first Monday after `protocol-v2` is tagged and the runner
  has completed one dry run without a hand fix. Earliest plausible: Nov 23 or Nov 30.
- **Checkpoints** then fall 13, 26 and 52 scored weeks after that Monday.

## Not verified

- Open-Meteo: when each AIFS run becomes available, and whether the forecast endpoint
  serves `ecmwf_aifs025_single` out to 168 hours at our points.
- EIA: the actual publication lag for PJM sub-BA load on a Sunday night.
- GitHub Actions: current limits on scheduled workflows and cache size for the weights.
- Cowork and cloud routines: what environment they provide and for how long.
