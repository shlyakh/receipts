# Google WeatherNext and NVIDIA forecasts as temperature inputs

Research note, 2026-11-13. Research only: nothing downloaded beyond bucket listings and
one README, nothing installed, no code changed. Complements
`notes/weather_skill_sensitivity.md` section 3 (not repeated here). Everything below
was fetched today unless marked (memory) or (search summary); "not verified" means the
page read did not state it.

## Summary and recommendation

- **Google has a real hindcast archive; NVIDIA does not.** The only archived forecasts
  from an NVIDIA model are FourCastNet v2-small runs that NOAA/CIRA produce and publish
  on AWS. FourCastNet 3 and Atlas have open weights but no public forecast archive, and
  running them needs a Linux machine with an NVIDIA GPU of about 40 GB. Not a Mac job.
- **Try first: the NOAA/CIRA bucket `noaa-oar-mlwp-data`, GFS-initialised runs of
  GraphCast (`GRAP_v100_GFS`) and FourCastNet v2-small (`FOUR_v200_GFS`).** One code
  path gives a Google model and an NVIDIA model, no account, no form, open licence,
  usable today. Cost: 6-hourly steps, 0.25° grid, deterministic, and an older
  generation of both models.
- **File the WeatherNext Data Request form today in parallel.** WeatherNext 2 was the
  best source in our own table (section 3), its Earth Engine archive covers 2022-01-01
  to today, and historic data is CC BY 4.0. Approval is quoted at 5 to 7 business
  days, so it cannot be the first thing tried.
- **WeatherNext 3 is the most interesting and the least safe.** Hourly steps,
  station-calibrated 2 m temperature at 0.05°, BigQuery tables reaching back to 2024.
  The model was published in September 2026, so its forecasts for late 2025 are
  retrospective runs. Whether its training data ends before our window is not
  verified. Until it is, WeatherNext 3 rows would break "no lookahead" in spirit.
- **Use the GFS-initialised folders, not the IFS-initialised ones.** Our oracle series
  is IFS-based (section 3), so IFS-initialised runs would be flattered, and the IFS
  folders have a five to eight week hole in May to July 2026.

### What exactly to fetch for the first path

- Bucket: `s3://noaa-oar-mlwp-data` (us-east-1, anonymous read).
- Files: `GRAP_v100_GFS/YYYY/mmdd/GRAP_v100_GFS_YYYYmmddhh_f000_f240_06.nc` and the
  same pattern under `FOUR_v200_GFS/`.
- Run per origin: origins are Monday 00:00 New York time (04 or 05 UTC). The Monday
  00 UTC file was uploaded at about 08 UTC on the day checked, so it was not public at
  the cutoff. The run that was public is **Sunday 12 UTC** (uploaded about 19:45 UTC).
  That run reaches 240 h, which covers cutoff + 168 h (lead 184 to 185 h).
- Variable: 2 m temperature only, at the grid cells for the six station points in
  `protocol.yaml`, lead steps 12 h to 186 h.
- Size: each file is 4.6 GB (FourCastNet) or 5.7 GB (GraphCast). Whole files for 48
  origins and two models would be about 500 GB. Read by HTTP byte range instead
  (h5netcdf over fsspec, one variable). One uncompressed 2 m temperature field set is
  about 170 MB per file; the actual chunk layout is not verified, so test on one file
  before looping.
- Known holes in the window 2025-11-01 to 2026-11-12 (folder listing, today): 21 days
  missing in both GFS-initialised folders. Sundays missing: 2026-05-10, 2026-06-28,
  2026-09-20. Mondays missing: 2026-06-15, 2026-07-20. Three origins therefore need a
  fallback (Sunday 00 UTC run) or are dropped. A day folder does not guarantee both
  runs: the 2026-11-10 12 UTC FourCastNet file was 108 MB against the usual 4.5 GB.
- Effort: half a day to one day, including a new protocol version and a
  `DEVIATIONS.md` line for the new regime and the interpolation rule.

## 1. Google: WeatherNext 3, WeatherNext 2, Gen, Graph

| Product | Where | Archive | Step and leads | Form | Status |
|---|---|---|---|---|---|
| WeatherNext 2 | Earth Engine `projects/gcp-public-data-weathernext/assets/weathernext_2_0_0`; BigQuery table `weathernext_2_0_0` via Analytics Hub (search summary); Zarr `gs://weathernext/weathernext_2_0_0/zarr` | 2022-01-01 to 2026-11-13 06 UTC (Earth Engine page) | 0.25°, runs at 00/06/12/18 UTC, 6-hourly to 15 days, 64 members plus mean | WeatherNext Data Request form; a separate request for the raw Zarr | kept for existing workloads, new work pointed to WeatherNext 3 (search summary) |
| WeatherNext 3 | BigQuery `weathernext_3_0_0_0p1deg` (19 surface variables) and `weathernext_3_0_0_0p05deg` (station-calibrated 2 m temperature and dew point); Zarr `gs://weathernext3_statistics_spatial/weathernext_3_0_0_statistics/zarr/` (statistics) and `gs://weathernext3_spatial/weathernext_3_0_0/zarr/` (64 members); Earth Engine id not stated | 2024 onward per the BigQuery guide: 8 runs a day in 2024 to 2025, 24 a day from 2026. Exact first date not stated | hourly steps; the 00/06/12/18 UTC runs reach 360 h, the others 48 h; mean and five percentiles in BigQuery, members only in Zarr | same form, 5 to 7 business days | current |
| WeatherNext Graph (GraphCast) | Earth Engine `.../assets/59572747_4_0`; Zarr `gs://weathernext/59572747_4_0/zarr` | 2020-01-01 to 2026-07-29, deprecated | 0.25°, 6-hourly to 10 days, deterministic | same form | ends before our last origins; not usable alone |
| WeatherNext Gen (GenCast) | Earth Engine (asset not read today) | not verified | 12-hourly (memory) | same form | not pursued: step too coarse |

- **Dissemination delay.** WeatherNext 2 reaches BigQuery and Earth Engine about 7.5
  hours after the run time; WeatherNext 3 about 8 hours for the four main runs. For a
  Monday 04 to 05 UTC cutoff, the newest run that was public is Sunday 18 UTC (out at
  about 01:30 to 02:10 UTC Monday).
- **Licence.** Historic data is CC BY 4.0 with a required citation that describes it as
  experimental and not validated for real-world use. Real-time data falls under a
  separate Google DeepMind experimental terms document (PDF, not read). The boundary
  is 48 hours on the WeatherNext 2 Earth Engine page and 1 hour in the BigQuery guide.
  CC BY permits commercial reuse with attribution; the pages do not discuss commercial
  products and send other uses to the WeatherNext contact address. A product that
  needs live forecasts would fall under the real-time terms: not verified.
- **Cost.** No price on any page read. BigQuery bills by bytes scanned; the guide says
  to filter on `init_time` (partition) and `geography` (cluster) and warns that a row
  limit does not reduce the bill. On-demand rate and free monthly allowance: (memory)
  about 6 USD per TiB after a free first TiB, to be checked. Earth Engine is free for
  noncommercial projects (memory). Raw Zarr reads from Cloud Storage may bill the
  reader's project: not verified.
- **Vertex AI.** Offers on-demand WeatherNext 2 inference on dedicated hardware as an
  early-access programme (search summary). Not needed for hindcasts that already exist.
- **Open-Meteo.** `google_weathernext2_ensemble` and the mean computed by Open-Meteo;
  only the 00 and 12 UTC runs, 6-hourly native, interpolated to hourly by default,
  15 days. Previous Runs coverage starts 2026-06-06 (section 3), about 42% of the year.
  Good for a quick partial check, not for the full window.
- **Not verified:** whether the WeatherNext 2 archive for 2025-11 onward holds the runs
  as issued or regenerated ones; WeatherNext 3 training cutoff and first archive date;
  the exact WeatherNext 2 BigQuery schema.

Sources: https://developers.google.com/weathernext/guides/dissemination ,
https://developers.google.com/weathernext/guides/bigquery ,
https://developers.google.com/weathernext/guides/research ,
https://developers.google.com/earth-engine/datasets/catalog/projects_gcp-public-data-weathernext_assets_weathernext_2_0_0 ,
https://developers.google.com/earth-engine/datasets/catalog/projects_gcp-public-data-weathernext_assets_59572747_4_0 ,
https://open-meteo.com/en/docs/google-weathernext-api

## 2. NVIDIA

### Archived forecasts: only through NOAA/CIRA

Bucket layout listed today (`https://noaa-oar-mlwp-data.s3.amazonaws.com/`):

| Folder | Model | Years present | Notes |
|---|---|---|---|
| `FOUR_v200_GFS`, `FOUR_v200_IFS` | FourCastNet v2-small (NVIDIA) | 2020 on (GFS), 2022 on (IFS) | 4.6 GB and 1.8 GB per file |
| `FOUR_v100_GFS` | FourCastNet v1 | 2020 to 2023 | stopped |
| `GRAP_v100_GFS`, `GRAP_v100_IFS` | GraphCast Operational (Google) | 2021 on, 2022 on | 5.7 GB and 2.9 GB per file |
| `PANG_v100_GFS`, `PANG_v100_IFS` | Pangu-Weather | 2020 on, 2022 on | 4.6 GB per file (GFS) |
| `AURO_v100_GFS`, `AURO_v100_IFS` | Aurora (Microsoft) | 2025-01-22 on | not in the README; 4.7 GB and 2.1 GB |
| `parquet/*_combined_all.parq` | reference indexes for lazy reading | files dated 2025-04-01 | probably stop before our window: not verified |
| `Derived/` | derived fields | from 2020 | not examined |

- Runs at 00 and 12 UTC, 6-hourly steps from 0 to 240 h, NetCDF, one file per run.
  2 m temperature is present for every model. Updated through today (2026-11-13).
- Coverage in our window: GFS folders miss 21 days, all between 2026-04-11 and
  2026-10-16. IFS folders miss 37 days (GraphCast) and 56 days (FourCastNet), mostly
  one block from 2026-05-13 to 2026-06-17 (to 2026-07-09 for FourCastNet).
- Licence: the AWS registry entry says open data with no restrictions on use; the
  README adds a standard NOAA no-warranty disclaimer and asks for a citation of the
  BAMS paper (doi 10.1175/BAMS-D-24-0057.1). The licences of the underlying weights
  (GraphCast weights are non-commercial, (memory)) could matter for a commercial
  product built on these outputs: not verified.
- No archive of FourCastNet 3, Atlas or CorrDiff output was found anywhere.

Sources: https://registry.opendata.aws/aiwp/ ,
https://noaa-oar-mlwp-data.s3.amazonaws.com/README.txt

### Running a model ourselves

| Model | What it is | Licence | Hardware stated |
|---|---|---|---|
| FourCastNet 3 | probabilistic global model, 0.25°, 6-hourly, 72 variables including 2 m temperature, trained on ERA5 | Apache 2.0 on Hugging Face and NGC; the hosted NIM container has its own NVIDIA terms | Linux, NVIDIA GPU; tested on A100, H100, L40S |
| Atlas | latent diffusion transformer, about 2.5 billion parameters plus a 1.8 billion decoder, 0.25°, 6-hourly, needs two input states 6 h apart, trained on ERA5 1980 to 2019 | NVIDIA Open Model License, described as usable commercially | Linux; A100, H100, L40S; Ampere, Hopper, Blackwell |
| CorrDiff | downscaling of a coarse field to kilometre scale (an ERA5-to-HRRR variant exists) | not read | not a forecast model; it would sit on top of one |
| earth2studio | the package that wires models to data sources (GFS, IFS, ERA5); also ships GraphCast Operational and AIFS | Apache 2.0; third-party models keep their own licences | recommends Ubuntu 24.04, Python 3.13, CUDA 13, one GPU with at least 40 GB, 128 GB disk |

- **Mac.** The install guide does not mention macOS, CPU-only use or MPS, and says
  most models need a GPU. Treat as not runnable on the laptop. Not tested.
- **Time.** The FourCastNet 3 paper and model card give under 4 minutes for a 60-day
  forecast of one member on one GPU, so a 7-day member is well under a minute
  (derived). Compute for 48 origins is trivial; the work is the Linux GPU setup.
- **Initial conditions.** earth2studio pairs FourCastNet 3 with a GFS analysis source
  and AIFS with an IFS source in its examples (search summary). How far back each
  source reaches was not verified; NOAA's GFS archive on AWS covers our window
  (memory).
- **Note.** The repository says the release after 0.20.0 will be 1.0.0 and will break
  compatibility; pin `earth2studio<=0.20.0`.
- Effort: one to two days plus a rented 40 to 48 GB GPU for a few hours. Belongs in
  its own environment, like `models_ff/`.

Sources: https://huggingface.co/nvidia/fourcastnet3 , https://arxiv.org/abs/2507.12144 ,
https://huggingface.co/nvidia/atlas-era5 , https://github.com/NVIDIA/earth2studio ,
https://nvidia.github.io/earth2studio/main/userguide/about/install/

## 3. Feasible paths compared

| Path | Effort | Catch |
|---|---|---|
| A. NOAA/CIRA bucket, GraphCast and FourCastNet v2-small, GFS-initialised | 0.5 to 1 day, start today | 6-hourly; 0.25°; deterministic; older models; 3 origins need a fallback; multi-GB files need range reads |
| B. WeatherNext 2, Earth Engine or BigQuery | form wait of 5 to 7 business days, then 0.5 to 1 day | 6-hourly; 0.25°; needs a Google Cloud project; 64 members to average unless the mean is used; being superseded |
| C. WeatherNext 3, BigQuery 0.05° table | same wait, then about half a day (one query per origin) | retrospective forecasts for 2025, training cutoff unknown; station calibration may have used the observations we would score against |
| D. FourCastNet 3 or Atlas run by us | 1 to 2 days plus GPU rental | no Mac; we become the forecast producer, so issue-time and input choices are ours to defend |
| E. Open-Meteo WeatherNext 2 mean | an hour | starts 2026-06-06 |

Catches common to A, B and D:

- **6-hourly to hourly.** Valid times fall at about 01, 07, 13 and 19 local time, so
  the afternoon maximum is never sampled and linear interpolation flattens it. Summer
  peak-load hours are the ones affected. Options: plain linear interpolation (what
  Open-Meteo does), or interpolate the difference from a diurnal shape taken from the
  current forecast regime. Either choice must be fixed in a new protocol version
  before scoring.
- **Grid against station.** 0.25° cells are about 25 km. Norfolk, Monmouth shore and
  Toms River sit on the coast, where the nearest cell can be mostly sea. Check the
  land-sea fraction or take the nearest land cell.
- **Truth and initial conditions from one system.** IFS-initialised runs share a
  system with our oracle series. GFS-initialised runs do not, and compare fairly with
  the current GFS-based regime.
- **Hard rule 3.** A new source is a new regime: every model gets the same series, and
  it is reported in its own rows, never mixed with `oracle` or `forecast`.

### Published 2 m temperature skill against IFS

Thin. No source read today gives a day 1 to 7 curve for 2 m temperature for any of
these models at our latitudes.

- Google's pages give counts of targets won and a 10 to 20% gain of WeatherNext 2 over
  Gen across variables; no 2 m temperature figure. WeatherNext 3 claims are about
  resolution and precipitation.
- FourCastNet 3 abstract and card: better than conventional ensembles, close to the
  best diffusion models; no system named, no 2 m temperature figure. Atlas card: no
  skill comparison.
- (search summary, papers not opened) A 2026 preprint at 1.5° reports 2 m temperature
  RMSE at 24 h of about 0.48 K for GraphCast against 0.54 K for IFS HRES, and at
  240 h about 2.4 K against 2.6 K, with the IFS ensemble mean best at 2.0 K.
- (search summary) arXiv 2508.15724: AI models except Pangu-Weather beat HRES on
  average 2 m temperature error at most leads, but HRES stays better on record-breaking
  heat and cold. Relevant here because load peaks ride on those days.
- FourCastNet v2-small 2 m temperature skill: nothing found. Expect it to be the
  weakest of the set (memory).
- Our own numbers remain the best evidence: section 3 has WeatherNext 2 mean at 37%
  below the current regime at day 7 on the 2026-06 subsample, and NOAA AIGFS, a
  GraphCast descendant with GFS initial states, at 28% below.

## 4. Recommendation in order

1. Path A now, as a new regime in a new protocol version, gate origins first.
2. Submit the WeatherNext Data Request form today (Yuri: it needs a Google account and
   a stated use, so it is his to send).
3. When access arrives, path B for the full window. Before any use of path C, get the
   WeatherNext 3 training cutoff and calibration period in writing from the paper
   (arXiv 2609.03582, not read) or the contact address.
4. Path D only if an NVIDIA-branded current model is wanted for the story. It adds a
   GPU dependency and no archive.

Open points for Yuri:

- Is "public at the cutoff" (Sunday 12 UTC run) or "started before the cutoff"
  (Monday 00 UTC run) the rule for this regime? The existing forecast regime uses the
  second and carries a latency caveat.
- Accept 6-hourly input with a fixed interpolation rule, or hold out for hourly
  WeatherNext 3?
- Is a commercial product in view? If so, the real-time WeatherNext terms and the
  GraphCast weights licence need a proper read.
