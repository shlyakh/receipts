# Handoff: where things stand (Fri Nov 13, 2026, evening)

Read this first when starting a new session, then `CLAUDE.md` (rules), `DECISIONS.md`
and `results/README.md` (all numbers). This file is a snapshot; when it disagrees with
the repository, the repository wins.

## State

- Everything is committed and pushed to `main`. Tags: `protocol-v1`, `protocol-v1.1`,
  `protocol-v1.2`, `protocol-v1.3`.
- The only uncommitted file is `.github/workflows/pages.yml` (automatic dashboard
  deploys). Pushing it needs `gh auth refresh -s workflow` from Yuri.
- After a reboot, local Langfuse needs restarting: start Docker, then
  `docker compose up -d` in `/Users/yuri/work/langfuse`.

## Where the dashboard lives

- GitHub Pages: https://shlyakh.github.io/receipts/ (branch `gh-pages`). Update with
  `git subtree push --prefix dashboard origin gh-pages` after committing.
- Development artifact: https://claude.ai/artifact/UyjuJT9VXa4bcjnSrFgmjr
- Tabs: The problem, Methods, Receipt, Leaderboard, Weather, New claims, How it works.
  Tour of 9 steps, video in `dashboard/tour.webm`.

## What the results say (48 scored weeks, PJM zones DOM and JC, week ahead)

1. **Primary (protocol-v1, frozen):** Chronos-2 with temperature against our lag
   regression with temperature, forecast weather: DOM 0.730 (0.665 to 0.805), worth
   switching; JC 0.817 (0.686 to 0.960), inconclusive.
2. **Against the field's standard (protocol-v1.1, secondary):** Chronos-2 against Tao's
   Vanilla Benchmark with trend: DOM 0.946 (0.885 to 1.011), JC 0.997 (0.903 to 1.088).
   The lead largely disappears. The trend term is now verified from the competition
   paper (`notes/hong2014_gefcom2012.md`).
3. **Weather sources (protocol-v1.2, secondary):** with ERA5 as the temperature truth
   and four sources (GFS/HRRR mix, ECMWF IFS, ECMWF AIFS, ERA5 as perfect weather),
   Chronos-2 and Vanilla with trend are level under every source (0.94 to 1.04), and on
   DOM the ratio climbs as weather improves. AIFS gives the lowest load error for every
   model; IFS was no better than GFS for load this year. AIFS rows cover 45 weeks.
4. **Correction made:** the series first called "oracle / reanalysis" is ECMWF IFS
   analysis, not ERA5. `REFERENCE.md`, `DEVIATIONS.md` and the dashboard say so; the
   frozen protocol files keep the old wording.
5. **New model rows (protocol-v1.3, secondary):** see the section at the end of this
   file.

## Open decisions (Yuri)

1. **protocol-v2.** Proposal: ERA5 truth, AIFS forecast weather, Vanilla with trend as
   the named primary baseline, Chronos-2 with temperature as challenger. Because we have
   already seen this comparison on DOM and JC, the recommended primary is on **new PJM
   zones** chosen by a stated rule before any model runs on them, with DOM and JC as
   development results and a **prospective weekly panel** (forecast before the week
   happens, read at fixed checkpoints such as 13, 26, 52 weeks) alongside. Not decided.
2. **TabPFN attribution.** Its licence asks for "Built with PriorLabs-TabPFN" where
   results are published. Needed on the dashboard if that row is shown.
3. **Blogs and newsletters for the scan.** A verified list is in
   `notes/blog_newsletter_sources.md`. Substack and Medium discourage AI crawlers in
   `robots.txt`; GitHub's Atom feeds are discouraged too (its API is the alternative).
   Yuri said he may explore feeds during the hackathon.
4. **Framework to explore.** Research recommends Nixtla first (MSTL, NHITS with future
   temperature), Darts second (`notes/framework_choice.md`). Needs its own environment.
5. **More weather models.** Google WeatherNext 2 needs a data request form with a wait
   of 5 to 7 business days (Yuri's step). GraphCast and FourCastNet forecasts are in a
   public NOAA bucket and could be tried now (`notes/weathernext_nvidia.md`).

## Saturday (hackathon)

- You.com provider for `/scan`, `/judge`, `/run-candidate`, and the comparison with the
  Claude-based runs already stored under `candidates/claude`, `scorecards/claude`,
  `evidence/claude`. No You.com code exists yet, by rule.
- Suggested pitch: the first baseline made the model look 27% better; the search for
  the field's standards closed most of that gap; better weather closes the rest.

## Leftovers

- `dashboard/story.html` is out of date (no Vanilla, weather or wording fixes).
- Figure improvements not yet done: per-week paired difference chart, lead-time curves
  for more pairs, SVG export (`notes/figure_presentation.md`).
- A station-observation check would show whether ERA5 as truth flatters AIFS.
- Yuri's steps: blind labels in `eval/label_sheet.md`; Langfuse Claude Code plugin;
  true Wi-Fi-off check of the dashboard; read the README prior-work disclosure.
- `README.md` status section predates protocol-v1.1 to v1.3.

## How work was split today

Build tasks were delegated to Opus 5.5 agents and research to the session model, to
save the session's usage limit. Each agent was told its file boundaries and to commit
only its own paths.

## Research notes written today

`notes/blog_newsletter_sources.md`, `notes/model_families.md`,
`notes/weather_skill_sensitivity.md`, `notes/figure_presentation.md`,
`notes/framework_choice.md`, `notes/weathernext_nvidia.md`, `notes/method_facts.md`,
`notes/hong2014_gefcom2012.md`.

## New model rows (protocol-v1.3, secondary)

Tagged `protocol-v1.3`; registers two rows under six weather settings (the v1 pair and
the four v1.2 sources). Results in `results/models_v13/` and the section
"Competition-grade LightGBM (protocol-v1.3, secondary)" of `results/README.md`.

- **`lightgbm_competition`: scored once.** Untuned LightGBM built like the BigDEAL 2022
  entry (91 calendar and temperature features, detrended log target, two years of
  history, no load input). Lower error than Chronos-2 with temperature in all 12
  zone-and-setting cells (1 to 6% with forecast weather, 8 to 19% with actual weather),
  but only one cell clears the 10% bar (a practical tie); the rest are inconclusive.
  Against the frozen lag regression: 0.57 to 0.78, beyond the bar everywhere. Against
  Vanilla with trend: 0.84 to 1.00. Forecast weather, v1 setting: DOM 715 MW (Chronos-2
  734, Vanilla with trend 776), JC 204 MW (218, 219).
- **`tabpfn_ts_v2_temperature`: registered, NOT scored.** About 50 hours on CPU for all
  six settings (624 windows at about 5 minutes). The run saves each finished cutoff and
  resumes after an interruption. Commands:

  ```
  git switch --detach protocol-v1.3
  uv run --project models_ff python models_ff/tabpfn_ts_v2.py scored   # rerun the same line to resume
  git switch main
  uv run --project core python -m harness.v13 score scored
  ```

  Or run `tools/run_tabpfn_scored.sh`, which does these steps, keeps the Mac awake,
  logs to `data/logs/` and returns to `main` when it stops.

  Then commit `results/models_v13/forecasts/tabpfn_ts_v2_temperature.parquet` and the
  rescored files. CPU-only is part of the registered definition; using the Mac GPU would
  need a new protocol version.
- The dashboard does not show the v1.3 rows yet.
- Open: whether a tuned LightGBM is worth a later protocol version.
