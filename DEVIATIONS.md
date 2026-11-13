# Deviations from protocol-v1

Dated changes to the frozen protocol. `protocol.yaml` is never edited; each change is a
new version file.

- **2026-11-13, protocol-v1.1** (`protocol-v1.1.yaml`): added two secondary rows,
  Tao's Vanilla Benchmark as written in Ziel and Liu (2016) and the same with a linear
  trend, after a search for the field's standard baselines showed the
  original baseline set came from a single recent study. The primary comparison, its
  baseline, bar, verdict rule and sentences are unchanged. The new rows were run on the
  gate origins first and on the scored origins once, after the tag `protocol-v1.1`.
- **2026-11-13, label correction (no protocol change):** the v1 regime `oracle`, described
  in `protocol.yaml` as "Archive (reanalysis) temperature" and in `REFERENCE.md` as ERA5,
  is ECMWF IFS 9 km operational analysis from Open-Meteo's archive (identical at every
  hour to `models=ecmwf_ifs` at all six stations; 1.1 to 1.7 °C RMSE from ERA5 per
  station). The v1 `forecast` regime is HRRR on lead day 1 and GFS on days 2 to 7. The
  frozen wording is a known misnomer; `protocol.yaml`, the v1 and v1.1 inputs and all
  their results are unchanged. `REFERENCE.md` is corrected.
- **2026-11-13, protocol-v1.2** (`protocol-v1.2.yaml`): added four secondary weather
  regimes with ERA5 as the declared temperature truth and as history in every one of
  them: `oracle_era5`, `forecast_gfs` (v1 forecast horizon), `forecast_ifs` (ECMWF IFS
  0.25°) and `forecast_aifs` (ECMWF AIFS Single), lead-matched as in v1. Rows: the lag
  regression with temperature, Vanilla with trend and Chronos-2 with temperature. The
  window-drop rule for these regimes is scoped per regime (AIFS lacks three scored
  weeks). The primary comparison, its sentences and every v1 and v1.1 row are unchanged.
  Gate runs first; the scored origins are run once, after the tag `protocol-v1.2`.
- **2026-11-13, source verified (no protocol change):** the linear trend in
  `vanilla_benchmark_trend` (protocol-v1.1), recorded at registration as found in search
  summaries only, is confirmed by the competition paper (Hong, Pinson and Fan 2014,
  section 2.3). No definition, row or result changes. See `notes/hong2014_gefcom2012.md`.
