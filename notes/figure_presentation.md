# Presenting the results: figures, skills and libraries

Research note, Nov 13, 2026. Nothing in `dashboard/` or the code was changed. Sources
are URLs with short paraphrases. Items marked "(fetched)" were opened today; items
marked "(from memory)" are standard references whose pages were not re-opened.

## Summary

The dashboard already does the main things right: the leaderboard is an interval plot
with a line at 1 and the 0.90 to 1.10 band shaded, the receipt puts claimed and measured
on one axis, regimes are never mixed, and the charts follow light and dark themes. The
gaps are in what is not shown and in a few encodings:

- The 48 per-week errors behind every interval are never drawn, so a reader cannot see
  whether a lead comes from most weeks or from a few.
- Ratios are on a linear axis that runs to 2.2, which squeezes the region that matters
  (0.6 to 1.1) into a third of the width.
- Rows are sorted by ratio, so the order changes with every toggle and the row that
  sorts to the top is Timestral, the one that is not out-of-sample.
- The result that most changes the reading (Chronos-2 against Vanilla with trend, 0.95
  and 1.00) appears only as two number tiles, not on the receipt's axis.
- There is no way to get a figure out for a paper or slide.

No external skill needs to be installed to fix these. The `dataviz` skill already listed
in this Claude Code session covers the web charts. One external skill is worth a trial
for paper figures (K-Dense `scientific-visualization`, MIT), mainly for its audit
scripts. The owner's `interactivedatastory` skill is tied to another site; its chart
patterns and QA ideas are reusable, the skill as a whole is not.

## Top 5 changes, ranked

| # | Change | Data | Effort |
|---|---|---|---|
| 1 | **Per-week paired difference chart** for the primary comparison (and for Chronos-2 against Vanilla with trend): 48 points per zone, model error minus baseline error, zero line, mean marked. | `windows.parquet`; needs a `build_data.py` export (about 100 numbers per pair) | Small to medium |
| 2 | **Rework the leaderboard forest plot**: log ratio axis, fixed row order grouped by model family, primary row set apart at the top, Timestral below a rule, "lower is better" on the axis, a caption that states what the bars are. Show both zones side by side for one regime. | Already in `data.js` | Small |
| 3 | **Put the second check on the receipt strip**: a third row, "measured against the field's standard", on the same axis as claimed and measured, labelled secondary. | Already in `data.js` (`vs_standard`) | Small |
| 4 | **Lead-time curves for more than one pair**: ratio by forecast day against the frozen baseline, against Vanilla with trend, and for the 48-hour gap, as small multiples with one shared axis. | In `stats.parquet`; `build_data.py` exports one pair only today | Small |
| 5 | **A paper and slide export path**: a "Download SVG" button per chart, and separately a script that draws the same three figures to PDF from the parquet files. | Existing files; the script needs matplotlib added to `core/` (owner's decision) | Medium |

Next in line: an hour-of-week error heatmap (medium, needs a new aggregate), the
q10 to q90 band on the week trace, a colour and shape system by model family, and
three small fixes (web fonts offline, text size on phones, the protocol label).

## 1. Skills and tooling for scientific figures

All repository facts below were fetched from GitHub on Nov 13, 2026, without login.
Star counts are as shown on the page that day.

### Already available in this session

- **`dataviz`** (listed among this session's skills). Its description covers any chart
  in any medium, including d3 and inline SVG, with a colour method that has a runnable
  validator, mark specifications, interaction rules and light and dark consistency. It
  was not loaded for this note because no chart was written. It is the first thing to
  use for changes to `dashboard/index.html`.

### External skills

| Skill | What it contains | Licence | Maintained | Verdict |
|---|---|---|---|---|
| **K-Dense `scientific-visualization`** https://github.com/K-Dense-AI/scientific-agent-skills (path `skills/scientific-visualization/`; the repo was renamed from `claude-scientific-skills`, and the old raw path now returns 404) | Create and audit figures in Matplotlib, Seaborn or Plotly. A six-step workflow (evidence and destination, honest encoding, accessibility, scoped styles, export with provenance, review). Scripts: `palette_audit.py` (contrast and greyscale separation), `image_metadata.py` (DPI, fonts in PDF), `export_plan.py` (check against dated publisher profiles), `figure_export.py` (export with a provenance manifest), style presets. Assets: three `.mplstyle` files, Okabe-Ito and Paul Tol palettes. Rules include: name the interval type and n, show gaps as gaps, declare log axes, embed fonts as Type 42. | MIT (skill frontmatter and repo) | Yes. Skill version 1.4, "last reviewed 2026-10-01". Repo version 2.72.0, 177 skills, 57k stars; newest commits Nov 9, 2026 are automated scan reports. | **Worth trying**, for the paper-figure path only. Install this one skill, not the 177. |
| **`interactive-blog`** https://github.com/StanAlt/interactivedatastory | See below. | MIT for code and docs; the Acadia name, logo and article text are excluded (`NOTICE.md`) | Three commits, Nov 7 to Nov 11, 2026 | Reuse ideas, do not install as is. |
| **Orchestra `academic-plotting`** https://github.com/Orchestra-Research/AI-Research-SKILLs (path `20-ml-paper-writing/academic-plotting/`) | Two workflows: architecture diagrams generated with the Gemini image API, and data charts in matplotlib and seaborn. Chart defaults: serif font at 10 pt, no top or right spine, Okabe-Ito palette, the paper's own method in one accent colour and baselines in grey, PDF export. Column widths for NeurIPS, ICML, ICLR, ACL, AAAI. | MIT | Release notes for v1.7.1 dated June 2026; 14.5k stars | Low priority. The diagram half needs a Gemini key and is not needed here. The "own method in colour, baselines grey" convention is worth copying. |
| **`figure-generation`** https://github.com/lingzhi227/agent-research-skills | Three phases: expand the request into a plotting spec, generate and run a matplotlib script with up to four retries, then look at the rendered PNG and correct it. Ten figure types aimed at ML papers. Rules: 300 DPI or vector, text at least 8 pt at print size, no title inside the figure (the caption carries it). Also a `table-generation` skill (booktabs tables). | **None stated** on the repo page | 12 commits, 464 stars; dates not shown | Do not copy. The render, look, correct loop is the useful idea and needs no skill. |
| **Anthropic `data-visualization`** and `create-viz` https://github.com/anthropics/knowledge-work-plugins (path `data/skills/`) | Chart selection table, matplotlib, seaborn and plotly code patterns, design principles (title states the finding, sort by value, bars start at zero, show uncertainty), accessibility checklist. | Apache-2.0 (repo) | Active; 35.7k stars | General-purpose; overlaps with the built-in `dataviz`. Not needed. |

Registry sites also list a `figure-results-review` skill
(`a-green-hand-jack/ml-research-skills`); the repository returned 404 today, so it is
unverified and not recommended. `anthropics/skills` has no charting skill named on its
front page.

### `StanAlt/interactivedatastory` in detail

One skill, `interactive-blog`, built for one site (React and Vite). It produces a
standalone data-driven article in nine phases: brief, research, analysis, narrative,
visualization, build, social image, test, ship. What is specific to that site: the
component and CSS conventions, post registration, a booking calendar embed, and a logo.
What carries over here:

- **A source ledger**: every number has a source object with publisher, date, URL, the
  exact figure and caveats. `dashboard/story.html` already has one.
- **A "forecast against measured" scale** in `references/chart-patterns.md`: a hatched
  band for the claimed range and a solid marker for the measured value. This is the
  receipt strip.
- **One meaning per colour**, fixed in writing before drawing; colour never the only cue.
- **A "read the chart values" table** under every chart.
- **Browser checks at 1440, 390 and 320 px**, asserting no console errors and no
  horizontal overflow (`scripts/qa.cjs`, Playwright).
- **Floors**: chart labels at least 13 px.

Its animated-hero rule (autoplay, including under reduced motion) suits a marketing
article more than a benchmark page and is not recommended here.

### Cautions before installing any third-party skill

- A skill can carry scripts that run locally. Read the `SKILL.md` and scripts first.
- Hard rule 9 (write our own code) applies to chart code as well: use a skill for its
  checks and guidance, not to paste its plotting code into `dashboard/`.
- The K-Dense skill asks to be cited (arXiv:2609.00065) if it materially contributes to
  a manuscript.
- Its pinned packages (matplotlib, seaborn, plotly, kaleido, pillow, pypdf) are not in
  `core/`. Only matplotlib and pillow are needed for the audit scripts; Kaleido needs a
  local Chrome and can be skipped.

## 2. Guidance on presenting model comparisons honestly

### General principles

- **Rougier, Droettboom, Bourne, "Ten simple rules for better figures"** (fetched)
  https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003833 .
  The rules most relevant here: decide the one message per figure, adapt to the medium
  (screen, slide and paper need different versions), write captions, do not accept
  library defaults, use colour with intent, do not mislead.
- **Wilke, Fundamentals of Data Visualization**, chapter on uncertainty (fetched)
  https://clauswilke.com/dataviz/visualizing-uncertainty.html . Every figure with
  error bars must say what they are and at what level. Overlap of two error bars is an
  unreliable test; plot an interval for the difference itself. Graded bars (two levels,
  the inner one thicker) reduce the reading of a bar as a hard limit. When several
  models are compared with one reference, say whether the intervals are adjusted for
  multiple comparisons. Other chapters (from memory): ratios belong on a log axis
  (`coordinate-systems-axes.html`), small multiples need shared axes
  (`multi-panel-figures.html`), encode a category in colour and a second cue
  (`redundant-coding.html`), label lines directly instead of using a legend.
- **Cleveland and McGill 1984** (from memory)
  https://doi.org/10.1080/01621459.1984.10478080 . Position on a common scale is read
  most accurately, then length, then angle and area, then colour. This is why a dot
  plot on one axis beats bars or colour-coded tables for a leaderboard.
- **Tufte, The Visual Display of Quantitative Information** (from memory)
  https://www.edwardtufte.com/ . Small multiples, removing ink that carries no data,
  and keeping the visual size of an effect proportional to the numerical size.
- **Nature research figure guide** (fetched)
  https://research-figure-guide.nature.com/figures/preparing-figures-our-specifications/ .
  Sans-serif type (Arial or Helvetica) at 5 to 7 pt, vector PDF or EPS with editable
  text, fonts embedded as Type 42, an accessible palette (it cites Wong 2011,
  https://doi.org/10.1038/nmeth.1618), no red and green pairing, axis labels with
  units, no background gridlines. The older author page
  (https://www.nature.com/nature/for-authors/final-submission) redirected to a login
  today and was not read.
- **Science** author instructions (from memory)
  https://www.science.org/content/page/instructions-preparing-initial-manuscript .
  Similar: vector formats, sans-serif type, figures legible at column width.
- **Colour**: Crameri, Shephard, Heron 2020 on rainbow and red-green maps (from memory)
  https://doi.org/10.1038/s41467-020-19160-7 . Use a perceptually uniform sequential
  map for a heatmap of error, and a diverging map centred on 1 for a heatmap of ratios.

### Chart forms for this benchmark

| Form | What the guidance says | Fit here |
|---|---|---|
| **Forest or interval plot with a reference line and an equivalence band** | The standard form for ratios in meta-analysis: point, interval, a line at no effect, a log axis so that 0.5 and 2.0 sit the same distance from 1 (Cochrane Handbook ch. 10, from memory, https://training.cochrane.org/handbook/current/chapter-10 ). Equivalence testing reads the interval against a band fixed in advance: wholly inside is equivalent, wholly outside is different, crossing is undecided (Lakens 2017, from memory, https://doi.org/10.1177/1948550617697177 ). | This is exactly the protocol's rule and the right main figure. The page has it; it needs the log axis and the fixes in section 4. |
| **Paired per-window differences** | Show the raw paired observations beside the summary interval ("estimation plots", Ho et al. 2019, from memory, https://doi.org/10.1038/s41592-019-0470-8 ; Weissgerber et al. 2015 on showing data instead of bars, https://doi.org/10.1371/journal.pbio.1002128 ). | The largest gap. The interval comes from resampling 48 weekly errors; draw them. |
| **Critical-difference diagrams** | Demšar 2006 (from memory, https://jmlr.org/papers/v7/demsar06a.html ) ranks models over many independent datasets. Benavoli et al. 2016 (https://jmlr.org/papers/v17/benavoli16a.html ) show the mean-rank test's verdict for a pair depends on which other models are included, and recommend pairwise tests. The M3 and M4 analyses use the related "multiple comparisons with the best" plot (Koning et al. 2005, https://doi.org/10.1016/j.ijforecast.2004.10.003 ; M4, https://doi.org/10.1016/j.ijforecast.2019.04.014 ). | **Not recommended.** Two zones are not "many datasets", the 48 weeks are not independent, ranks discard the size of the effect that the 10% bar is about, and it would add a test the protocol does not name. |
| **Skill by lead time** | Forecast evaluation reports accuracy by horizon because averages over the horizon hide where a method wins (Hyndman and Athanasopoulos, from memory, https://otexts.com/fpp3/accuracy.html and https://otexts.com/fpp3/tscv.html ). Scaled errors and ratios to a naive method are the convention (Hyndman and Koehler 2006, https://doi.org/10.1016/j.ijforecast.2006.03.001 ). | The page has it for one pair. Extend to the pairs that matter. |
| **Error by hour of week heatmap** | Usual in load forecasting, where error concentrates at peaks and ramps (Hong and Fan 2016 review, from memory, https://doi.org/10.1016/j.ijforecast.2015.11.011 ). | New. A 7 by 24 grid per model and zone; ratio version with a diverging scale centred on 1. |
| **Claimed against measured** (dumbbell or two-row strip) | Two values of the same quantity on one axis, joined or stacked, each with its own interval, with the setup difference stated beside it. | The receipt has it. Add the third row and label the claimed interval's level. |
| **Small multiples** | Same axes repeated, so the eye compares panels directly (Tufte; Wilke). | Replace the zone and regime toggles with panels where width allows. Regimes stay in separate panels (hard rule 4). |

### Conventions in forecasting leaderboards

- **fev-bench** (fetched, https://arxiv.org/html/2509.26468 ). Reports two numbers per
  model: a skill score (1 minus the geometric mean of error ratios to seasonal naive,
  ratios clipped to 0.01 to 100) and a win rate over pairwise comparisons. Intervals
  come from resampling tasks 1,000 times, at 95%. The paper states that intervals are
  most meaningful for pairwise quantities, and its first figure shows pairwise win
  rates and skill scores with intervals. It also reports a leakage percentage per
  model. Code: https://github.com/autogluon/fev .
- **GIFT-Eval** (fetched, https://arxiv.org/html/2410.10393 ). Errors are scaled by
  seasonal naive; models are ranked within each of 97 configurations and the ranks
  averaged; results are also broken out by domain, horizon and frequency. Leaderboard
  (from memory): https://huggingface.co/spaces/Salesforce/GIFT-Eval .
- **What this implies here.** Ratio to a named baseline with a pairwise bootstrap
  interval is the current convention, and this project already follows it. Two
  conventions it does not yet show: a column for leakage beside every foundation-model
  row in the figure itself (the data has `n_after` of `n`), and a seasonal-naive
  reference so readers from those leaderboards can place the numbers (MASE is in
  `leaderboard.parquet`).
- **Statistical precipice** (Agarwal et al. 2021, from memory,
  https://arxiv.org/abs/2108.13264 ). With few runs, report interval estimates and not
  point rankings. Same message: the interval, not the order of rows, is the result.
- **Diebold and Mariano 1995** (from memory,
  https://doi.org/10.1080/07350015.1995.10524599 ) is the classical pairwise test of
  forecast accuracy. The whole-week bootstrap plays that role here; no second test
  should be added to a figure.

## 3. Libraries

### For the static page (no build step, works offline)

Sizes are the minified single-file builds listed by the jsDelivr package API today;
licences from the npm registry.

| Library | Version | Size (min) | Licence | Offline, no build | Notes |
|---|---|---|---|---|---|
| d3 | 7.9.2 (7.9.0 vendored) | 281 KB | ISC | Yes, already in `dashboard/vendor/` | Full control; everything recommended in section 4 can be drawn with it. SVG output, so export is direct. |
| Observable Plot | 0.6.19 | 212 KB | ISC | Yes, one UMD file; needs d3 loaded first | Much less code for dot, rule, facet and cell marks; built-in facets (small multiples) and log scales. SVG output. Styling through CSS variables takes some care. The one addition worth considering. |
| Vega-Lite (+ Vega + vega-embed) | 6.5.0 / 6.4.0 / 7.3.0 | 258 + 521 + 60 = 839 KB | BSD-3-Clause | Yes, three files | Declarative JSON specs; built-in SVG and PNG export; specs can be shared with Altair for paper figures. Heavier, and theming for light and dark is by config object, not CSS. |
| ECharts | 6.1.0 | 1.12 MB | Apache-2.0 | Yes | Canvas by default (an SVG renderer exists). Good for dashboards with many interactions; interval plots need custom series. Too heavy for this page. |
| uPlot | 1.6.32 | 51 KB | MIT | Yes | Very fast canvas time series only. Canvas means no vector export. Not needed at 168 points. |
| Plotly | 4.3.0 | 4.84 MB (basic bundle 1.20 MB) | MIT | Yes | Built-in PNG and SVG download; large, and its look is hard to bring in line with the page. |
| Chart.js | 4.6.1 | 210 KB | MIT | Yes | Canvas; no native interval or forest plot. Not suitable. |

Recommendation: stay on d3. Add Observable Plot only if the number of small-multiple
charts grows enough that hand-written d3 becomes the cost. Do not add a canvas library:
every chart here has under a few thousand marks, and SVG is what makes export simple.

### For paper-style static figures (Python)

None of these is installed in `core/` today (its dependencies are pandas, pyarrow,
statsmodels, lightgbm and so on; no plotting package). Adding one is `uv add` in
`core/` and is the owner's decision.

| Library | Licence | Notes |
|---|---|---|
| matplotlib | Matplotlib licence (BSD-compatible) | The baseline choice. Vector PDF and SVG, exact physical size, Type 42 fonts with `pdf.fonttype: 42`. Enough by itself for the three figures. |
| SciencePlots (fetched, https://github.com/garrettj403/SciencePlots ) | MIT | Matplotlib style sheets: `science`, `ieee`, `nature`, `notebook`, and a colour-blind-safe `bright` cycle. Requires LaTeX unless combined with the `no-latex` style. Must be imported before use since 2.0. 9.4k stars. A handful of rcParams in a local `.mplstyle` does the same without the dependency. |
| seaborn (objects interface) | BSD-3-Clause | Convenient facets and `so.Range` / `so.Dot` for interval plots. Its own bootstrap must not be used: intervals have to come from `stats.parquet`. |
| plotnine | MIT | Grammar of graphics; `geom_pointrange` with `facet_grid` gives the forest plot in a few lines. Pulls in more dependencies. |
| Altair | BSD-3-Clause | Produces Vega-Lite specs, so one spec could serve the page and the paper. Offline PNG, SVG and PDF export needs `vl-convert-python`. Only worth it if the page moves to Vega-Lite. |

Recommendation: plain matplotlib with a small project style file, reading
`stats.parquet`, `leaderboard.parquet` and `windows.parquet` directly. It draws
precomputed numbers only.

## 4. Review of the current dashboard and proposed changes

### What exists (`dashboard/index.html`)

| Chart | Where | Notes |
|---|---|---|
| US and zone maps | Story tab | Context only. |
| One-week trace: actual, regression, Chronos-2 | Story tab | 12 of the 48 weeks (every fourth), forecast regime, two models, no quantile band. Legend above the chart. |
| Receipt strip per zone: claimed and measured with intervals, band shaded | Receipt tab | Linear axis fixed at 0.6 to 1.2. |
| "Against the field's standard" | Receipt tab | Two number tiles, no chart. |
| Ratio by forecast day, DOM and JC | Receipt tab | Chronos-2 with temperature against the frozen baseline only. Shared y-axis, band shaded. |
| Leaderboard interval plot and table | Leaderboard tab | One zone and one regime at a time, sorted by ratio, linear axis 0.4 to at least 2.2. |

`dashboard/story.html` is a second, scrolling version with its own strip and day
charts; the same points apply.

### What is done well

- Interval plot, reference line at 1 and the pre-registered band are all present.
- Regimes are never in one row.
- The flagged model is drawn hollow and grey.
- A table of values sits under the leaderboard chart.
- Colours come from CSS variables, so charts follow the light and dark themes.

### Issues found

1. **No per-week data anywhere.** `windows.parquet` has 2,304 rows; none reach the page.
2. **Linear ratio axis with a long right tail.** With the domain 0.4 to 2.2, the span
   0.6 to 1.1 gets under 30% of the plot width. On a linear axis 0.5 and 2.0 are not
   symmetric about 1.
3. **Row order changes with the toggle**, because rows are sorted by ratio. A reader
   comparing DOM with JC has to find each model again.
4. **Timestral sorts to the top.** The visually leading row is the one the project says
   cannot be told apart from leakage.
5. **The primary comparison is marked only by a slightly larger dot and bold text.**
6. **The axis has no title and no direction cue** ("ratio to regression + temperature;
   lower is better"). The caption for what the bars are is in the Methods tab only.
7. **Intervals for ten models against one baseline are unadjusted.** That is correct for
   the one primary comparison, but the figure should say that the other rows are
   secondary and not adjusted.
8. **The claimed interval is not labelled** on the strip (the GB study's 0.931 to
   1.001). Per `notes/moran.md` it is also a 90% interval, but over 960 resampled days,
   against 48 resampled weeks here. Say both in the row labels, so the narrower claimed
   bar is read as more data, not as a stronger result.
9. **The second check has no figure**, although it changes the reading more than
   anything else on the page.
10. **Colour carries three ideas at once**: role (baseline orange, primary blue), family
    (foundation models blue) and status (flagged grey). LightGBM, Vanilla and seasonal
    naive share a grey with no distinction. Univariate rows, which hard rule 3 requires
    to be labelled, are marked only in the label text.
11. **Text size on phones.** The week chart has a 960-unit viewBox with 12 px text, so
    at 390 px wide the text renders at about 5 px. Only the leaderboard has a narrow
    layout.
12. **Web fonts are loaded from Google Fonts**, the one thing on the page that is not
    offline. It falls back to system fonts, so nothing breaks, but an exported SVG will
    not match.
13. **No export.** Inline SVG uses `var(--name)` colours, which do not survive being
    saved as a file.
14. **The page says "protocol-v1"** (header and `data.js`) while the Vanilla rows are
    protocol-v1.1.

### Proposed changes, in priority order

Effort: small is under an hour of chart code; medium is a few hours including a
`build_data.py` change and a check on both themes and a phone width.

**A. Per-week paired differences (top 1).**
- Shows: for each of the 48 scored weeks, the model's weekly error minus the
  baseline's, in MW or as a percentage of the baseline's mean error. Points along time
  (x is the week) with a zero line and the mean drawn as a line, plus a compact strip of
  the same points at the right. One panel per zone, forecast regime. Second pair:
  Chronos-2 with temperature against Vanilla with trend.
- Why: the mean of these differences divided by the baseline's mean error is the ratio
  minus 1, so the figure shows directly what the bootstrap resamples. It also shows
  season (heat waves on JC) and the two gaps at the clock changes.
- Data: `windows.parquet` columns `model, unique_id, regime, cutoff, mae`. Needs
  `build_data.py` to export weekly `mae` for four models in two zones (about 400
  numbers). Display only; no new statistic.
- Effort: small to medium.

**B. Leaderboard forest plot rework (top 2).**
- Log x-axis with ticks at 0.5, 0.67, 0.8, 0.9, 1.0, 1.1, 1.25, 1.5, 2.0.
- Fixed row order in every view: the primary row first and separated by space; then
  foundation models with temperature; classical models with temperature; a rule; models
  without weather; a rule; "not out-of-sample" (Timestral) last.
- Two panels side by side (DOM, JC) sharing the row labels, one regime at a time; the
  regime toggle stays. On a phone the panels stack.
- Axis title with direction; a one-line caption under the chart: dot is the ratio of
  mean weekly error, bar is the 90% whole-week bootstrap interval over 48 weeks, band is
  the pre-registered 0.90 to 1.10, only the first row is the primary comparison, other
  rows are secondary and unadjusted.
- A small "unseen weeks 48/48" column at the right of each foundation-model row, as
  fev-bench does with its leakage column.
- Optional: draw a 50% interval as a thicker inner bar. This needs a new percentile
  from the bootstrap, which is a harness change, so leave it out unless wanted.
- Data: all in `data.js` (`board`). Effort: small.

**C. Receipt strip with the second check (top 3).**
- Three rows on one log axis per zone: claimed in GB; measured against the frozen
  baseline (primary, solid); measured against Vanilla with trend (secondary, lighter or
  hollow, labelled "secondary").
- State each interval's level and sample in the row label (90%, 960 days; 90%, 48
  weeks). Put both zones in one figure with a
  shared axis so DOM and JC can be compared.
- Data: `claim`, `board`, `vs_standard`, all in `data.js`. Effort: small.

**D. Lead-time curves for the pairs that matter (top 4).**
- Small multiples, rows are zones, columns are: against the frozen baseline; against
  Vanilla with trend; cost of the 48-hour gap. Same y-axis (log), band shaded, day 1 to
  day 7. Points with intervals; keep the connecting line thin, since days are ordered.
- Data: `stats.parquet` has per-day ratios with intervals for kinds `vs_baseline`,
  `vs_vanilla_trend` and `gap48_cost`. `build_data.py` exports only one pair today; widen
  the filter. Effort: small.

**E. Export for paper and slides (top 5).**
- In the page: a "Download SVG" link per chart that clones the SVG, replaces each
  `var(--x)` with its computed value, sets a font stack and a background, and saves.
  Printing to PDF from the browser then also works. Effort: small.
- Outside the page: a script (for example `tools/figures.py`) that reads the parquet
  files and writes figures A, B and C as PDF at single-column and slide sizes, with one
  style file. Needs matplotlib in `core/`. Effort: medium. This is where the K-Dense
  skill's `palette_audit.py` and `image_metadata.py` checks would be used.

**F. Error by hour of week.**
- Shows: a 7 by 24 grid of mean absolute error for one model, and a second grid of the
  ratio to the baseline on a diverging scale centred on 1. Answers "is the lead at the
  peaks or overnight".
- Data: needs hourly errors aggregated from `results/forecasts/*.parquet` and the
  actuals: 168 cells per model, zone and regime. `build_data.py` states that it computes
  nothing new, so the aggregate belongs in the harness's statistics step, written to
  `results/`, and then exported. Local-time alignment at the clock changes needs care.
- Effort: medium. No intervals per cell (48 values each); say so in the caption.

**G. Week trace improvements.**
- Add the q10 to q90 band for Chronos-2 (the forecasts file has `q10`, `q90`), and a
  thin residual panel below (forecast minus actual) so the two models can be compared
  without reading two near-identical lines. Offer all 48 weeks, not every fourth.
- Label the lines at their right end instead of the legend.
- Data: `build_data.py` change; all 48 weeks adds roughly 500 KB to `data.js` unless
  values are rounded to 10 MW or loaded per zone. Effort: medium.

**H. One colour and shape system, written down first.**
- Colour is the model family: foundation model, classical with temperature, no weather.
  Emphasis is the role: the primary pair at full strength, everything else muted (the
  "own method in colour, baselines grey" convention).
- Shape is the second cue: filled circle for models with temperature, open circle for
  univariate; a different mark (for example a diamond with a dashed interval) for "not
  out-of-sample", so open circles are not used for two meanings.
- Check the palette in both themes and for colour-blind separation; the `dataviz`
  skill has a validator for this. Effort: small.

**I. Small fixes.**
- Vendor the two fonts or drop the Google Fonts link (offline, and stable export).
- Give the week and day charts a narrow layout, or a minimum rendered text size of
  about 11 px.
- Show the protocol version per row (v1 or v1.1) instead of one page-wide label.
- Add an optional switch on the leaderboard for the reference: frozen baseline or
  Vanilla with trend (`stats.parquet` kind `vs_vanilla_trend` covers the models). Keep
  the frozen baseline as the default and label the other view secondary (hard rule 11).

### What not to add

- **Critical-difference diagrams or rank tables**: wrong unit of analysis here (see
  section 2).
- **Bars for error**: a bar from zero adds ink without information when the quantity of
  interest is a ratio near 1.
- **A single figure mixing regimes**: against hard rule 4.
- **New tests or intervals computed in the page**: every drawn number should come from
  `results/`, as now.
