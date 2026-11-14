# Zone selection for the protocol-v2 primary comparison

Written 2026-11-13. Research note. No forecasting model was run for it:
every number below is a description of the load series or a fact from a PJM report.

**Decision (Yuri, 2026-11-13, decision 33):** AEP and AE are the protocol-v2 primary
zones. AE was kept over PEP to preserve JC's summer-peaking shape.

## How the selection was made

1. Listed every PJM sub-BA that EIA-930 serves (20 zones) and downloaded hourly load for
   each, 2023-11-01 to 2026-11-13 (`tools/zone_selection/download.py`).
2. Checked data quality with the v1 load rules, written afresh: missing hours, zeros,
   flagged values, held values, and how many of the 52 scored weeks each zone keeps.
   Quality turned out identical across zones, so it does not drive the choice.
3. Computed load statistics per zone on 2023-11-01 to 2025-10-31 only, the two years
   before the first scored origin (`tools/zone_selection/stats.py`).
4. Wrote the rule below, applied it, and read off one pick and one runner-up per slot.
5. Cross-checked eight zones for level breaks and confirmed that the DOM and JC downloads
   match the repository's processed load exactly (`tools/zone_selection/check.py`).
6. Looked up background on territories and data-centre load in PJM reports.

No forecasting model was fitted or run on any new zone at any step. The rule and its
two thresholds were written with all 20 load series in view; that is disclosed in the
protocol.

## Recommendation

| Slot | Pick | Runner-up | Why |
|------|------|-----------|-----|
| Like DOM | **AEP** (American Electric Power) | AP (Allegheny Power) by the rule; CE (ComEd) by data-centre load | Same size as DOM (15.8 against 15.2 GW mean), the only other zone growing fast (6% and 9% a year against 8% and 9%), winter peak equal to summer peak as on DOM, and the second-largest data-centre load in PJM |
| Like JC | **AE** (Atlantic City Electric) | PE (PECO) by the rule; PEP (Pepco) if more independence from JC is wanted | The only other zone of usable size with JC's shape: summer peak 1.66 times the winter peak (JC 1.70), flat load, coastal New Jersey, mostly residential and commercial |

The AEP pick is clear on every measure. The AE pick depends on one judgment: AE borders
JC and its daily load moves with JC's (correlation 0.93). See "The JC slot" below.

## Proposed rule (for `protocol-v2`)

> For each development zone (DOM, JC), the primary zone is the PJM sub-BA in EIA-930 with
> the smallest standardised distance to it on seven load statistics computed over
> 2023-11-01 to 2025-10-31 (before the first scored origin): log mean load, growth of
> shoulder-month load, summer/winter peak ratio, summer/shoulder and winter/shoulder mean
> ratios, weekday/weekend ratio, and mean daily minimum/maximum. Excluded: DOM and JC
> themselves, zones whose daily load anomaly correlates 0.95 or more with the development
> zone, zones with mean load under 1,000 MW, and zones whose scored weeks do not pass the
> v1 load rules. The next zone in the same ordering is the runner-up, used only if the
> pick fails a gate for data reasons.

What it selects: DOM slot AEP (distance 1.56; next AP 3.06, ATSI 3.29, CE 3.46). JC slot
AE (2.12; PS 2.43 is excluded at correlation 0.98; next PE 2.63, PEP 2.94). Dropping the
size term from the distance gives the same picks and runner-ups.

## The zones

EIA-930 lists 20 PJM sub-BAs (`facets[parent][]=PJM`, endpoint in `REFERENCE.md`; facet
names `parent` and `subba` confirmed against the live API). UGI and OVEC, which PJM
reports separately, are not in the EIA list. EIA codes differ from PJM's: AP = APS,
BC = BGE, CE = COMED, DAY = DAYTON, DUQ = DLCO, JC = JCPL, ME = METED, PE = PECO,
PEP = PEPCO, PN = PENLC.

### Data availability, 2023-11-01 to 2026-11-11

Identical for all 20 zones:

- The only missing hours are the UTC days around each daylight-saving change (146 hours
  in 6 runs, 0.55% of hours). These are the same hours in every zone, as `protocol.yaml`
  already records for DOM and JC.
- No zero or negative values, no duplicates, no value flagged by the v1 flag rule, no
  level break in quarterly means for the zones checked (DOM, JC, AEP, AE, CE, AP, PE, PEP).
- Under the v1 drop rule every zone keeps 48 of the 52 scored weeks and drops the same
  four (2026-03-02, 2026-03-09, 2026-10-26, 2026-11-02).
- Runs of six or more identical consecutive values: JC 29 hours, ME 84, PL 97, PN 94,
  RECO 6, none elsewhere. Small, but it shows some zones report rounded or held values.
- My DOM and JC downloads equal `data/processed/load.parquet` at all 26,400 common hours.

So data quality does not separate the zones; every zone passes.

### Load statistics

Years run November to October: Y1 2023-11 to 2024-10, Y2 2024-11 to 2025-10, Y3 2025-11
to 2026-10. Y3 overlaps the scored window and is shown for information only; the rule
uses Y1 and Y2. Growth is not weather-adjusted. "Shoulder" is April, May and October.
Peaks and ratios are over Y1 and Y2, local time. S/W = summer (Jun to Aug) maximum over
winter (Dec to Feb) maximum. Min/max = mean of daily minimum over daily maximum. LF =
mean over maximum. Peak hour = hour of the average daily peak, summer / winter.

| Zone | Territory | Mean Y2, MW | Growth Y2 | Growth Y3 | Shoulder growth Y2 | S/W peak | Summer/ shoulder | Winter/ shoulder | Wkday/ wkend | Min/ max | LF | Peak hr |
|------|-----------|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----|
| **DOM** | Dominion, Virginia and NE North Carolina | 15,153 | 7.8% | 9.2% | 6.7% | 0.96 | 1.27 | 1.20 | 1.04 | 0.75 | 0.59 | 18 / 8 |
| **JC** | Jersey Central P&L, New Jersey | 2,525 | 0.1% | 2.4% | -0.3% | 1.70 | 1.55 | 1.23 | 1.06 | 0.64 | 0.41 | 18 / 19 |
| AE | Atlantic City Electric, southern New Jersey | 1,146 | -1.9% | 0.9% | -4.6% | 1.66 | 1.62 | 1.20 | 1.03 | 0.63 | 0.42 | 19 / 19 |
| AEP | AEP: Ohio, W. Virginia, SW Virginia, Indiana, Michigan, Kentucky, Tennessee | 15,783 | 6.2% | 9.1% | 4.6% | 0.99 | 1.21 | 1.21 | 1.07 | 0.77 | 0.65 | 18 / 9 |
| AP | Allegheny Power: W. Maryland, N. West Virginia, SW Pennsylvania | 5,738 | 2.1% | 2.7% | -0.2% | 0.92 | 1.23 | 1.32 | 1.07 | 0.75 | 0.57 | 18 / 9 |
| ATSI | FirstEnergy Ohio and Penn Power | 7,766 | 1.7% | 1.2% | -1.2% | 1.19 | 1.25 | 1.18 | 1.09 | 0.75 | 0.61 | 17 / 19 |
| BC | Baltimore Gas & Electric | 3,460 | -0.1% | 3.0% | -5.6% | 1.05 | 1.41 | 1.35 | 1.05 | 0.70 | 0.51 | 18 / 19 |
| CE | ComEd, northern Illinois | 10,903 | 2.8% | 0.9% | 0.0% | 1.42 | 1.35 | 1.17 | 1.09 | 0.74 | 0.50 | 18 / 19 |
| DAY | Dayton, Ohio | 2,015 | 1.8% | 2.1% | -0.3% | 1.07 | 1.27 | 1.21 | 1.12 | 0.72 | 0.59 | 18 / 10 |
| DEOK | Duke Energy Ohio and Kentucky | 3,032 | 1.4% | 0.6% | -3.2% | 1.06 | 1.32 | 1.21 | 1.07 | 0.72 | 0.58 | 18 / 9 |
| DPL | Delmarva: Delaware, Maryland and Virginia Eastern Shore | 2,102 | 1.3% | 1.7% | -1.4% | 1.00 | 1.45 | 1.41 | 1.05 | 0.68 | 0.51 | 18 / 8 |
| DUQ | Duquesne, Pittsburgh | 1,498 | -2.1% | -0.9% | -7.1% | 1.27 | 1.35 | 1.18 | 1.05 | 0.75 | 0.57 | 18 / 19 |
| EKPC | East Kentucky Power Cooperative | 1,658 | 2.4% | 1.7% | -0.6% | 0.71 | 1.28 | 1.50 | 1.03 | 0.66 | 0.43 | 18 / 8 |
| ME | Met-Ed, SE Pennsylvania | 1,779 | -1.2% | 0.5% | -4.5% | 1.09 | 1.28 | 1.27 | 1.12 | 0.73 | 0.57 | 18 / 19 |
| PE | PECO, Philadelphia | 4,427 | 0.8% | 1.9% | -1.9% | 1.26 | 1.39 | 1.26 | 1.07 | 0.71 | 0.51 | 18 / 19 |
| PEP | Pepco: Washington DC and Maryland suburbs | 3,273 | 1.3% | 1.1% | -1.8% | 1.07 | 1.39 | 1.29 | 1.07 | 0.69 | 0.52 | 18 / 8 |
| PL | PPL, central and eastern Pennsylvania | 4,769 | 1.3% | 1.3% | -1.9% | 0.93 | 1.25 | 1.32 | 1.08 | 0.74 | 0.58 | 18 / 19 |
| PN | Penelec, western and northern Pennsylvania | 1,942 | -1.1% | 0.2% | -2.1% | 0.99 | 1.19 | 1.26 | 1.11 | 0.78 | 0.65 | 19 / 19 |
| PS | PSE&G, northern and central New Jersey | 4,847 | -1.0% | 2.2% | -2.2% | 1.51 | 1.44 | 1.18 | 1.08 | 0.72 | 0.48 | 18 / 19 |
| RECO | Rockland Electric, NE New Jersey | 171 | 1.3% | 1.0% | -0.8% | 1.87 | 1.49 | 1.10 | 1.10 | 0.68 | 0.39 | 17 / 19 |

Peaks over Y1 and Y2, MW (summer / winter): DOM 23,905 / 24,957; JC 6,234 / 3,658;
AEP 23,366 / 23,670; AE 2,742 / 1,650. The DOM summer figure equals the 2025 summer
peak PJM reports for the zone.

### Closeness to DOM and JC

Distance = Euclidean distance on the seven statistics after standardising each across
the 20 zones. Correlation = correlation of daily mean load, each day divided by its
29-day centred mean, Y1 and Y2. Shape = RMSE between normalised average daily profiles
(summer and winter together).

| Zone | Dist. to DOM | Corr. with DOM | Shape to DOM | Dist. to JC | Corr. with JC | Shape to JC |
|------|-----:|-----:|-----:|-----:|-----:|-----:|
| AEP | **1.56** | 0.77 | 0.019 | 5.38 | 0.65 | 0.077 |
| AP | 3.06 | 0.85 | 0.023 | 4.73 | 0.74 | 0.064 |
| ATSI | 3.29 | 0.63 | 0.043 | 4.31 | 0.67 | 0.073 |
| CE | 3.46 | 0.48 | 0.048 | 3.61 | 0.51 | 0.061 |
| PL | 3.68 | 0.79 | 0.036 | 4.52 | 0.84 | 0.078 |
| PE | 3.73 | 0.86 | 0.046 | 2.63 | 0.94 | 0.061 |
| DEOK | 3.88 | 0.68 | 0.037 | 3.52 | 0.60 | 0.062 |
| PEP | 3.96 | 0.94 | 0.031 | 2.94 | 0.84 | 0.061 |
| PS | 4.32 | 0.76 | 0.049 | 2.43 | 0.98 | 0.052 |
| DAY | 4.35 | 0.64 | 0.039 | 4.30 | 0.62 | 0.066 |
| PN | 4.52 | 0.64 | 0.049 | 5.35 | 0.66 | 0.098 |
| DPL | 4.65 | 0.94 | 0.038 | 3.39 | 0.85 | 0.049 |
| BC | 4.90 | 0.94 | 0.031 | 3.57 | 0.87 | 0.048 |
| DUQ | 5.16 | 0.71 | 0.044 | 4.19 | 0.71 | 0.069 |
| EKPC | 5.17 | 0.66 | 0.044 | 5.13 | 0.43 | 0.070 |
| ME | 5.21 | 0.79 | 0.035 | 4.46 | 0.86 | 0.064 |
| AE | 6.55 | 0.79 | 0.070 | **2.12** | 0.93 | 0.039 |
| RECO | 6.86 | 0.68 | 0.076 | 3.39 | 0.92 | 0.038 |

DOM to JC is 5.28, so the two development zones are themselves far apart.

## What "similar" should mean

- **DOM**: very large, load growing several percent a year from data centres, hence a
  flat daily profile and a trend that a short training window lags; winter peak about
  equal to summer peak; a wide territory needing several weather points.
- **JC**: mid-size, flat load, residential and commercial, strongly summer-peaking with
  a low load factor, coastal.

Background from PJM's own reports (descriptive, published before this work):

| Zone | Data-centre load at the July 2025 peak, MW | 10-year summer peak growth forecast | Residential / commercial / industrial | PJM weather stations |
|------|-----:|-----:|------|------|
| DOM | 5,563 (68% of PJM's) | 5.4% | 34 / 56 / 10 | IAD, RIC, ORF |
| AEP | 1,726 (21%) | 5.3% | 35 / 29 / 37 | FWA, CAK, CMH, CRW, ROA |
| CE | 623 (8%) | 3.9% | 33 / 36 / 32 | ORD |
| PS | 255 (3%) | 2.4% | 35 / 56 / 9 | EWR |
| AP | 0 reported | 2.9% | 39 / 21 / 40 | PIT, IAD |
| JC | 0 reported | 1.0% | 49 / 42 / 9 | EWR, ACY |
| AE | not listed | 0.1% | 45 / 45 / 9 | ACY |
| PE | 0 reported | 1.8% | 39 / 22 / 39 | PHL |
| PEP | 0 reported | 2.0% | 39 / 59 / 2 | DCA |

Sources: PJM 2026 Load Forecast Report, January 2026 (zonal dashboards, pages 14 to 34)
https://www.pjm.com/-/media/DotCom/library/reports-notices/load-forecast/2026-load-report.pdf
and PJM Load Forecast Accuracy Report, May 2026 (page 6)
https://www.pjm.com/-/media/DotCom/planning/res-adeq/load-forecast/2026-load-forecast-accuracy-report.pdf

### The DOM slot

AEP is the nearest zone by a wide margin and matches on each property separately: size,
measured growth, seasonal balance, daily shape (the closest profile of any zone), and it
is the only other zone with a large measured data-centre load. It is not a copy of DOM:
correlation 0.77, a different region and weather, and a much larger industrial share
(37% against 10%).

Runner-up: the rule gives AP. AP borders DOM, shares the Dulles weather station in
PJM's mapping, and is not growing, so it is "like DOM" in shape only. CE is the
alternative if the slot is read as "data-centre zone": third-largest data-centre load,
but it is summer-peaking (1.42), its measured growth is small (2.8%, then 0.9%), and it
is in the Central time zone, so the origin "Monday 00:00 America/New_York" would fall at
23:00 on Sunday local time.

### The JC slot

Only four zones are strongly summer-peaking: RECO (1.87), JC (1.70), AE (1.66), PS
(1.51); CE (1.42) is next. RECO is 171 MW, too small to be a benchmark. PS interleaves
with JC's territory and tracks it almost exactly (0.98). That leaves AE: same state,
same coast, same seasonal shape, 45% of JC's size.

The cost is independence. AE borders JC, PJM maps Atlantic City airport to both, and the
daily correlation is 0.93. No eastern zone is independent of JC (PE 0.94, BC 0.87, DPL
0.85, PEP 0.84), and the scored weeks are the same weeks, so some dependence is
unavoidable; the threshold is where the judgment lies:

| Correlation limit | Pick | Runner-up |
|------|------|------|
| 0.95 (proposed) | AE | PE |
| 0.90 | PEP | DPL |

PEP, DPL and BC are coastal or tidewater and similar in size to JC, but none is
summer-peaking in these two years (S/W 1.07, 1.00, 1.05), which is JC's defining trait.
PE is summer-leaning (1.26) but 39% industrial and almost as correlated with JC as AE is.

## Practical points for the picks

- **Weather points** (to be written into the protocol; the v1 zone series is an
  unweighted mean). AEP: PJM's five stations are Fort Wayne, Akron-Canton, Columbus,
  Charleston WV and Roanoke. An unweighted mean will not match where the load is (Ohio
  carries the data-centre growth); the same simplification already applies to DOM. AE:
  PJM uses Atlantic City only; one or two more points (for example Vineland and Cape
  May) would follow the v1 pattern of three. Coordinates need to be chosen and checked.
- **AIFS coverage** for new points has not been checked (v1.2 lost 3 scored weeks for
  DOM and JC).
- **Time zone**: I believe all of AEP's PJM territory keeps Eastern time, not verified.
- **Size and noise**: AE is the smallest zone above the 1,000 MW floor, so its relative
  errors will be larger than JC's.

## Not verified, and limits

- The rule, its seven statistics and its thresholds were written today with all 20
  series in view. No forecast was run, but the rule is not blind to the descriptive
  data, and the 0.95 and 1,000 MW limits were set knowing what they admit.
- `protocol-v2-draft.yaml` says the zone list is written "before fetching their load".
  For this note the load of all 20 zones (2023-11 to 2026-11) was downloaded to a
  scratch directory and described, including the scored year for the quality checks.
  Nothing was added to `data/raw` or the manifest. Yuri should decide whether that
  wording still holds or should become "before any model runs on them".
- Growth figures are raw, not weather-adjusted. Shoulder-month growth is the less
  weather-driven version; on it only DOM (6.7%) and AEP (4.6%) grow.
- PJM's data-centre figures are utility-reported; BGE's is withheld, and zones shown as
  0 may simply not have reported. AE has no page in the accuracy report.
- EIA-930 history before 2023-11 was not downloaded for the new zones; v1 starts in
  2019. Only the two years of history that the models need were checked.
- Chronos-2 and the other pretrained models may have seen earlier years of AEP and AE
  load, as for DOM and JC.
- Territory descriptions are from the PJM zone map and general knowledge of the
  utilities, not from a tariff document.

## Reproducing

```
uv run --project core python tools/zone_selection/download.py   # skips files already present
uv run --project core python tools/zone_selection/stats.py
uv run --project core python tools/zone_selection/check.py
```

- Raw downloads: `data/zone_selection_raw/` (git-ignored, 120 files), with SHA-256 hashes
  in `results/zone_selection/raw_manifest.json`. `stats.py` refuses to run if a file does
  not match. This is separate from `fetch.py` and `data/raw`; the harness never reads it.
- Outputs, committed: `results/zone_selection/zone_stats.csv` (every statistic and both
  distances per zone), `anomaly_corr.csv`, `shapes.csv`, `pjm_zones.json`.
- Rerun on 2026-11-13 from the repository: the three output files are identical to the
  ones the research produced, and the rule returns AEP (1.56) and AE (2.12).
