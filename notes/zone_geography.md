# Zone geography: territories, PJM's weather stations, v2 weather points, map outlines

Written 2026-11-13. Research note for protocol-v2 (zones AEP and AE, decision 33) and
for the dashboard maps. No forecasting model was run. Facts are paraphrased; sources are
listed at the end and referred to as [S1] .. [S10].

## Short answers

- **Is AE one town?** No. The AE zone is Atlantic City Electric's whole territory: about
  575,000 customer accounts in eight counties of southern New Jersey (Atlantic, Cape
  May, Cumberland and Salem, and parts of Gloucester, Camden, Burlington and Ocean),
  roughly 2,700 square miles [S3][S6][S10]. PJM uses a
  single weather station for it (Atlantic City airport), which is probably where the
  "one town" impression comes from.
- **Is Roanoke AEP or Dominion?** AEP. Roanoke and most of southwest Virginia are
  Appalachian Power territory, an AEP operating company. PJM itself assigns the Roanoke,
  Lynchburg and Blacksburg-Christiansburg-Radford metro areas to the AEP zone and uses
  Roanoke airport as one of the zone's five weather stations [S1]. The dot on the map
  was right; shading all of Virginia as DOM was wrong.
- **Right weather points for v2:** the benchmark does not use weather stations; a
  weather point is an ERA5 grid cell (0.25 degree). Recommended: the cells that contain
  PJM's own stations for the zone, with PJM's own weights (section 3). AEP: five cells.
  AE: one cell, a land cell about 16 km inland of Atlantic City.

## 1. What each zone covers

Customer counts are accounts in EIA Form 861 for 2025 (Sales to Ultimate Customers,
bundled plus delivery-only) [S3]. They cover the investor-owned utilities only.

| Zone | PJM name [S2] | Utilities (EIA number) | States | Accounts, 2025 | Main load centres |
|------|---------------|------------------------|--------|---------------:|-------------------|
| DOM | Dominion Virginia Power zone | Virginia Electric & Power Co (19876), trading as Dominion Energy Virginia and Dominion Energy North Carolina | VA, NE North Carolina | 2.81 million (VA 2.68 m, NC 0.13 m) | Northern Virginia (data centres), Richmond, Hampton Roads |
| JC | Jersey Central Power & Light zone | Jersey Central Power & Lt Co (9726), a FirstEnergy company | NJ | 1.18 million | Two separate blocks: Morris/Sussex/Warren/Hunterdon in the north-west, Monmouth/Ocean on the shore |
| AEP | American Electric Power zone | Appalachian Power (733), Indiana Michigan Power (9324), Ohio Power (14006, includes the former Columbus Southern), Kentucky Power (22053), Kingsport Power (10331), Wheeling Power (20521) | OH, WV, VA, IN, MI, KY, TN | 3.38 million (Ohio Power 1.54 m, Appalachian 0.97 m, Indiana Michigan 0.62 m, Kentucky 0.16 m, Kingsport 0.05 m, Wheeling 0.04 m) | Columbus, Canton, Fort Wayne, South Bend, Charleston, Huntington, Roanoke, Lynchburg, Kingsport |
| AE | Atlantic Electric zone | Atlantic City Electric Co (963), an Exelon (Pepco Holdings) company | NJ | 0.58 million | Atlantic City and the shore towns, Vineland-Bridgeton, the Camden/Gloucester suburbs |

What was checked, and how:

- **AEP sub-zones.** PJM's Load Forecast Report lists Appalachian Power, Columbus
  Southern Power, Indiana Michigan Power, Kentucky Power and Ohio Power as sub-zones of
  AEP [S2]. Kingsport and Wheeling are not listed as sub-zones; they are AEP operating
  companies that report PJM as balancing authority to EIA [S3], and Appalachian Power's
  own fact page counts Tennessee in its three-state territory (1.1 million customers, 57
  counties, head office in Charleston, W.Va.) [S7]. Their membership of the AEP zone is
  inferred from that, not read from a PJM zone definition.
- **Metro areas PJM ties to each zone** (economic inputs of the 2026 forecast) [S1]:
  AEP = Columbus, Canton-Massillon, Weirton-Steubenville, Fort Wayne, Elkhart-Goshen,
  Muncie, South Bend-Mishawaka, Niles-Benton Harbor, Charleston, Beckley,
  Huntington-Ashland, Roanoke, Lynchburg, Blacksburg-Christiansburg-Radford,
  Kingsport-Bristol. AE = Atlantic City-Hammonton, Vineland-Bridgeton and the
  Lakewood-New Brunswick division. JC = Newark, Lakewood-New Brunswick, Camden, Trenton
  divisions. DOM = the state of Virginia.
- **Embedded cooperatives and municipals.** A PJM zone is the transmission owner's
  area, so load served by others inside it counts. Dominion states that PJM's DOM
  forecast covers the whole zone including cooperatives such as Northern Virginia
  Electric Cooperative and Mecklenburg Electric Cooperative [S8]. In EIA-861 the
  municipal systems of Salem, Radford, Martinsville and Danville (Virginia) and Vineland
  (New Jersey, 26,000 accounts) report PJM as balancing authority; Bristol Virginia
  Utilities reports TVA [S3]. No public list was found that ties each cooperative or
  municipal to a zone, so the map outlines use the investor-owned utilities only (see
  section 4).
- **AE and JC overlap on the map, not on the ground.** Both utilities list Burlington
  and Ocean counties. By area in the territory polygons (section 4), Ocean is mostly
  JC with AE in the south, and Burlington is split between AE, JC and a third utility.

## 2. Weather stations PJM uses

PJM builds each zone's weather as a weighted average of airport stations. The weights
are supplied by the distribution companies and published in Table 3 of the 2026
Long-Term Load Forecast Supplement (page 8) [S1]. Manual 19 (revision 39, June 2026) no
longer carries the table and points to the Supplement [S4].

| Zone (PJM code) | Station | Weight | Lat, lon | ERA5 grid cell used by Open-Meteo |
|-----------------|---------|-------:|----------|-----------------------------------|
| AE | ACY Atlantic City International | 100% | 39.45, -74.57 | 39.50, -74.50 (land) |
| AEP | CMH Columbus (John Glenn) | 23.4% | 39.99, -82.88 | 40.00, -83.00 (land) |
| AEP | FWA Fort Wayne | 22.7% | 40.97, -85.21 | 41.00, -85.25 (land) |
| AEP | CRW Charleston, W.Va. (Yeager) | 22.6% | 38.38, -81.59 | 38.50, -81.50 (land) |
| AEP | ROA Roanoke | 16.2% | 37.32, -79.97 | 37.25, -80.00 (land) |
| AEP | CAK Akron-Canton | 15.1% | 40.92, -81.44 | 41.00, -81.50 (land) |
| DOM (VEPCO) | IAD Washington Dulles | 33.3% | 38.93, -77.45 | 39.00, -77.50 (land) |
| DOM (VEPCO) | ORF Norfolk | 33.3% | 36.90, -76.19 | 36.75, -76.25 (nearest cell 37.00, -76.25 is sea) |
| DOM (VEPCO) | RIC Richmond | 33.3% | 37.51, -77.32 | 37.50, -77.25 (land) |
| JC (JCPL) | EWR Newark | 75% | 40.68, -74.17 | 40.75, -74.25 (land) |
| JC (JCPL) | ACY Atlantic City International | 25% | 39.45, -74.57 | 39.50, -74.50 (land) |

Coordinates are the NOAA National Weather Service station records
(`api.weather.gov/stations/K<code>`), rounded to two decimals [S5]. They are the
observing sites at the airports, not the FAA airport reference points; the two differ by
a kilometre or two at most, far less than the 0.25 degree weather grid.

Two things stand out. PJM's JC stations are both outside JC territory (Newark is PSE&G,
Atlantic City airport is AE). And PJM's DOM stations are the same three places the
benchmark already uses.

Grid cells come from live requests on 2026-11-13 (archive API, `models=era5`, one per
point). "Land" means the default request (which prefers a land cell) returned the same
cell as `cell_selection=nearest`. The AEP points and ACY also return complete AIFS
forecasts at lead days 1 and 7 from the Previous Runs API (`ecmwf_aifs025_single`), on
the same cells.

## 3. Recommended weather points for protocol-v2

The benchmark uses no weather stations. A **weather point** is an ERA5 grid cell (0.25
degree), named by its cell centre as Open-Meteo returns it with `models=era5`. PJM's
stations only tell us which cells to take.

**Rule: for each primary zone, the weather points are the ERA5 cells that Open-Meteo
resolves PJM's Load Forecast Supplement Table 3 stations (2026 edition) to, each with
PJM's weight for that station. Requests are made at the cell centre. Zone temperature =
weighted mean of the series at those cells.**

| Zone | Weather point | Cell centre lat | Cell centre lon | Elevation, m | Land cell | Weight | PJM station inside it |
|------|---------------|----:|----:|----:|-----|-------:|-----|
| AEP | columbus | 40.00 | -83.00 | 247 | yes | 0.234 | CMH |
| AEP | fort_wayne | 41.00 | -85.25 | 236 | yes | 0.227 | FWA |
| AEP | charleston_wv | 38.50 | -81.50 | 332 | yes | 0.226 | CRW |
| AEP | roanoke | 37.25 | -80.00 | 315 | yes | 0.162 | ROA |
| AEP | akron_canton | 41.00 | -81.50 | 332 | yes | 0.151 | CAK |
| AE | atlantic_city_inland | 39.50 | -74.50 | 14 | yes | 1.000 | ACY |

Checked live on 2026-11-13, one archive request per cell centre (`models=era5`, one
day): each returns 24 hourly values and its own coordinates, with the default land
preference and with `cell_selection=nearest` alike, which is what "land cell" means
here. The same six centres return complete AIFS forecasts (`ecmwf_aifs025_single`,
Previous Runs API, lead days 1 and 7) on identical coordinates, so truth and forecast
sit on one grid.

Elevation is what Open-Meteo returns for the requested coordinate (its 90 m terrain
model at the cell centre), not ERA5's own model height. Open-Meteo adjusts temperature
to that elevation, so the request coordinate is part of the definition: asking at the
airport instead of the cell centre gives the same cell but a slightly different series
(Charleston's airport is at 265 m, the cell centre at 332 m). Fixing the request at the
cell centre removes that choice.

Why this rule: it is published, it comes from the utilities that know where their load
is, and it leaves us no choice to make after seeing the data. The alternatives:

| Option | For | Against |
|--------|-----|---------|
| (i) Cells of PJM's stations, PJM's weights (recommended) | Published and load-representative; nothing hand-picked | Needs weights in the protocol and a weighted mean in the weather processing (today it is unweighted); AE rests on one grid cell |
| (ii) Cells of PJM's stations, unweighted | No code change | Drops information for no gain. For AEP it barely matters: over 2025 the weighted and unweighted ERA5 series differ by 0.16 °C RMSE (largest hourly gap 0.9 °C; computed with requests at the airport coordinates), because the weights are all between 15% and 23% |
| (iii) Hand-picked cells at load centres, as for DOM and JC | Can follow the load (for AE one could add Vineland and the Camden/Gloucester suburbs) | A researcher's choice made with the zones' load already in view; hard to defend for a primary zone |
| (iv) Area- or population-weighted grid average | Closest to "the zone's weather" | With Open-Meteo it is one request per grid cell and per source: about 330 cells of 0.25 degrees for AEP and about 12 for AE (estimated from territory area), for ERA5 and again for each forecast source and lead day, plus a population grid for the weights. A different method from v1, so v1 and v2 would no longer be comparable |

The five AEP weather points are far apart in climate as well as distance: mean 2025
temperature runs from 10.5 °C (Akron-Canton) to 14.4 °C (Roanoke), and the five differ
by 6 °C on an average hour. Roanoke correlates least with the others (0.90 to 0.96). So
the zone needs all five; a single central point would not do.

The draft protocol lists approximate city coordinates under `pjm_weather_stations` (for
the map). They are not weather points in the sense above. Its Atlantic City coordinate
(39.36, -74.42, the town on the barrier island) has a sea cell (39.25, -74.50) as nearest
neighbour; only Open-Meteo's default land preference moves it to 39.50, -74.50. Its
Charleston coordinate rounds to a different cell from the airport's. Naming the cells
directly removes both problems.

### Should DOM and JC be re-pointed?

Today both use three hand-picked coordinates with equal weights (`REFERENCE.md`), each
resolved by Open-Meteo to a grid cell. No re-pointing is recommended, so no new cells
are proposed for them.

- **DOM: no change needed.** The three v1 points (Richmond, Norfolk, Dulles; equal
  weights) are PJM's three places with PJM's equal weights, 2 to 11 km from the
  airports. That is the same grid cell or, for Richmond, probably the neighbouring one
  (by rounding; the v1 point was not re-queried). DOM already follows the rule in
  substance.
- **JC: keep the v1 points and say so.** PJM's mapping (Newark 75%, Atlantic City 25%)
  would be a real change, and both stations lie outside the territory. JC is a
  development zone in v2, never read as the primary result, and every v1 number was
  produced with the current points. Recommended: keep them, record in the protocol that
  JC is the one zone not on PJM's mapping, and if cheap add one secondary row with JC on
  PJM's mapping to show how much it matters.

## 4. Zone outlines for the dashboard

Built by `tools/zone_selection/build_zone_map.py` into `dashboard/zones.js` (211 KB):
`window.ZONES` (per zone: `name`, `utilities`, `fips`, `shared`, `filled`) and
`window.COUNTIES`, a TopoJSON of the 882 counties of NJ, PA, MD, DE, DC, VA, WV, OH, IN,
MI, KY, TN and NC in the same pre-projected Albers coordinates and the same transform as
`dashboard/us.js`. Nothing was simplified or re-quantised: the file is us-atlas
`counties-albers-10m` with the other states' counties and unused arcs removed.

Rules, applied in this order:

1. A county belongs to a zone if one of the zone's utilities lists it in the EIA-861
   Service Territory file for 2025 (the latest year). Dominion is limited to Virginia
   and North Carolina (its 2025 list adds two West Virginia counties where it has no
   retail customers).
2. The lists are self-reported and contain strays (Dominion lists Bristol, Buchanan and
   several North Carolina counties that share a name with a Virginia county). Each
   claim is checked against the utility's polygon in the ORNL/HIFLD retail service
   territory layer: a county the polygon covers less than 2% of is dropped. Where a
   polygon is missing for a whole state (Indiana Michigan Power in Michigan) the list
   is kept untested. A county still claimed by two of our zones goes to the zone whose
   polygon covers more of it and is listed under `shared` for both.
3. Virginia independent cities left without a zone (Appalachian Power's 2025 list has
   none; its 2024 list had Roanoke, Lynchburg and Galax) go to the zone whose polygon
   covers at least half of the city, or else to the zone of the neighbouring counties
   when they agree. They are listed under `filled`. Bristol is left out because its
   municipal utility reports TVA as balancing authority.

Embedded cooperatives and municipals are not added. The outline is therefore the
investor-owned utilities' counties; cooperative territory inside a listed county is
shaded with it, and counties served only by cooperatives are not shaded.

Result:

| Zone | Counties | By state |
|------|---------:|----------|
| DOM | 104 | VA 87, NC 17 |
| JC | 12 | NJ 12 |
| AEP | 155 | OH 51, VA 33, WV 25, KY 19, IN 18, MI 6, TN 3 |
| AE | 7 | NJ 7 |

Checks passed: Roanoke city and Roanoke County in AEP; Atlantic and Cape May in AE;
Fairfax and Loudoun in DOM; Monmouth and Ocean in JC. No county is in two zones' `fips`.

Ambiguous or partly served counties:

- **Claimed by two zones** (share of the county's area in each polygon): Burlington NJ
  (AE 0.46, JC 0.17, drawn AE); Ocean NJ (JC 0.63, AE 0.21, drawn JC); Albemarle (DOM
  0.61, AEP 0.24), Appomattox (DOM 0.52, AEP 0.14), Campbell (DOM 0.79, AEP 0.41) and
  Pittsylvania (DOM 0.47, AEP 0.33), drawn DOM; Amherst (AEP 0.92, DOM 0.03), Botetourt
  (AEP 0.46, DOM 0.24) and Tazewell (AEP 1.00, DOM 0.99), drawn AEP. Area is not load:
  Campbell's population sits next to Lynchburg on the Appalachian side. Tazewell's
  Dominion polygon looks like an error in the layer; the county is Appalachian
  territory.
- **Dropped as strays** (35 claims): for DOM, 8 North Carolina counties (Beaufort,
  Brunswick, Cabarrus, Cumberland, Granville, Hyde, Person, Warren) and in Virginia
  Accomack, Bedford, Buchanan, Carroll, Clarke, Franklin County, Greene, Henry, Madison,
  Nelson, Page, Rappahannock, Warren, Bristol and Falls Church (Falls Church is
  refilled by rule 3); for AEP, Hamilton, Henry, Howard, LaGrange, Miami, Steuben and
  Tipton (Indiana), Owsley (Kentucky), Logan and Summit (Ohio), Buckingham and Fluvanna
  (Virginia). Some of these are real slivers of service (Clarke, Page, Warren), mostly
  cooperative country.
- **Kept although the polygon covers under half the county** (61 counties: AEP 32, DOM
  23, JC 6), for example Essex, Mercer and Union NJ for JC (mostly PSE&G), Stark and
  Richland OH for AEP (shared with Ohio Edison), Louisa and Spotsylvania VA for DOM
  (mostly Rappahannock Electric Cooperative). The full list is printed by the script.
- **Filled cities**: Roanoke, Salem, Lynchburg, Galax, Danville (polygon), Radford,
  Martinsville, Norton (neighbours) to AEP; Falls Church and Franklin city to DOM.
  Winchester and Bristol have no zone. Danville's municipal system is in PJM but its
  zone was not confirmed.

Inputs (downloaded into the scratch directory, not the repository):

| File | Source | SHA-256 |
|------|--------|---------|
| `f8612025.zip` (Service_Territory_2025.xlsx, data year 2025) | `https://www.eia.gov/electricity/data/eia861/zip/f8612025.zip` | `f59f6c732bf685fe0a1591b32227f5ce572dc0dfd26bb5caaeed128ac4e3a396` |
| `counties-albers-10m.json` | `https://cdn.jsdelivr.net/npm/us-atlas@3/counties-albers-10m.json` | `a674dfa31b625e92635f32684a61ae135b05a91507f17f2d5164833237fecf46` |
| `counties-10m.json` (unprojected, for the area shares) | `https://cdn.jsdelivr.net/npm/us-atlas@3/counties-10m.json` | not recorded |
| nine utility polygons, layer year 2020 | PNNL mirror of HIFLD Electric Retail Service Territories [S9], one query per EIA number | printed by the script |

To rebuild: `uv run --project core python tools/zone_selection/build_zone_map.py <scratch dir>`
(downloads whatever is missing; about 30 seconds).

## 5. Not verified

- Kingsport Power and Wheeling Power as part of the AEP zone: inferred (AEP companies,
  PJM balancing authority), not read from a PJM zone definition.
- Which cooperatives and municipals are inside each zone, beyond the two Dominion
  names. In particular Rappahannock Electric Cooperative and Shenandoah Valley Electric
  Cooperative have territory in both the DOM and the Allegheny (APS) zones, and
  Danville's zone is unconfirmed.
- The HIFLD polygons are a 2020 layer taken from a mirror (the original site closed in
  2025). They are used only to drop strays and break ties. Their Indiana Michigan Power
  polygon stops at the Michigan line, and the Tazewell overlap suggests other errors.
- The two-decimal coordinates are NWS station records. FAA airport reference points
  were not looked up.
- "Land cell" is inferred from Open-Meteo returning the same cell with and without its
  land preference; Open-Meteo does not publish the land-sea mask in the response.
- The grid-cell counts in option (iv) are estimates from territory area.
- The 0.16 °C weighted-versus-unweighted figure is ERA5 for 2025 only, from requests at
  the airport coordinates (same cells, slightly different elevation adjustment); the
  forecast sources were not compared.
- The elevation column is Open-Meteo's terrain height at the cell centre, not ERA5's
  model orography, which Open-Meteo does not return.
- The cells of the existing DOM and JC points were not re-queried.
- Whether PJM's 2025 or earlier Supplements used the same stations and weights. The
  rule cites the 2026 edition.
- Square miles for AE come from an older company filing quoted in search results; the
  account counts are EIA's, and "customers" there means accounts, not people.
- The hand-picked AE alternatives in option (iii) were not tested against Open-Meteo.

## Sources

- [S1] PJM, 2026 Long-Term Load Forecast Supplement (February 2026), Table 3 "Weather
  Station Assignment" (p. 8) and "Economics Zonal Geographic Assignment" (p. 57):
  https://www.pjm.com/-/media/DotCom/planning/res-adeq/load-forecast/load-forecast-supplement-2026.pdf
- [S2] PJM, Load Forecast Report, January 2026, "TO Zones and Sub-Zones":
  https://www.pjm.com/-/media/DotCom/library/reports-notices/load-forecast/2026-load-report.pdf
- [S3] EIA, Form EIA-861 detailed data files, 2025 (Service Territory, Sales to Ultimate
  Customers): https://www.eia.gov/electricity/data/eia861/
- [S4] PJM Manual 19, Load Forecasting and Analysis, revision 39 (effective 2026-06-30):
  https://www.pjm.com/-/media/DotCom/documents/manuals/m19.ashx
- [S5] NOAA National Weather Service station records, for example
  https://api.weather.gov/stations/KACY (same pattern for KCAK, KCMH, KCRW, KFWA, KROA,
  KEWR, KIAD, KORF, KRIC)
- [S6] New Jersey Board of Public Utilities, Atlantic City Electric infrastructure
  filing summary (eight counties, about 565,000 customers):
  https://www.nj.gov/bpu/pdf/announcements/aceinfrastructure.pdf
- [S7] Appalachian Power, company facts: https://appalachianpower.com/info/facts/
- [S8] Dominion Energy, integrated resource plan stakeholder question on the DOM zone
  forecast (seen as a search-result summary; the page itself did not load its text):
  https://devirp.dominionenergy.com/stakeholder-questions-and-answers/Do-you-include-the-entire-DOM-Zone-within-PJMs-load-forecast
- [S10] Atlantic City Electric, 2011 annual report filing (territory of about 2,700
  square miles in eight counties; seen as a search-result summary):
  https://sec.gov/Archives/edgar/data/8192/000119312511080773/0001193125-11-080773.txt
- [S9] Electric Retail Service Territories (ORNL for HIFLD), PNNL mirror:
  https://eedgis.pnnl.gov/arcgis/rest/services/Hosted/Electric_Service_Territories/FeatureServer/0
- Open-Meteo archive and Previous Runs APIs (endpoints in `REFERENCE.md`), queried
  2026-11-13.
