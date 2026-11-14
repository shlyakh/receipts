"""County outlines of the four benchmark zones for the dashboard map.

Writes dashboard/zones.js with
  window.ZONES    = {DOM|JC|AEP|AE: {name, utilities, fips, shared, filled}}
  window.COUNTIES = TopoJSON (us-atlas counties-albers-10m, cut down to the map's states)

A zone is drawn as the counties its investor-owned utilities report serving in EIA
Form 861 (Service Territory file). Rules, in order:

1. A county belongs to a zone if one of the zone's utilities lists it (STATES limits a
   utility to the states where it has retail customers).
2. The lists are self-reported and contain strays, so each claim is checked against the
   utility's polygon in the ORNL/HIFLD retail service territories: a county the polygon
   covers under MIN_SHARE of is dropped from that zone. Where a utility's polygon is
   missing for a whole state (Indiana Michigan Power in Michigan) its list is kept as it
   is. A county still claimed by two of our zones goes to the one whose polygon covers
   more of it, and is recorded under `shared` for both.
3. A Virginia independent city left without a zone (the lists often omit them) goes to
   the zone whose polygon covers at least half of it, or else to the zone of its
   neighbouring counties when they all agree (recorded under `filled`). Bristol is left
   out: its municipal utility reports TVA, not PJM, as balancing authority (EIA-861).

Embedded cooperatives and municipals are not added: no public county list ties them to a
PJM zone. They sit inside the outline wherever the investor-owned utility lists the county.

Usage: uv run --project core python tools/zone_selection/build_zone_map.py <scratch dir>
Inputs are downloaded into <scratch dir> when missing. See notes/zone_geography.md.
"""

import hashlib
import io
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
import requests

YEAR = 2025
EIA_URL = f"https://www.eia.gov/electricity/data/eia861/zip/f861{YEAR}.zip"
ATLAS_URL = "https://cdn.jsdelivr.net/npm/us-atlas@3/{name}"
HIFLD_URL = (
    "https://eedgis.pnnl.gov/arcgis/rest/services/Hosted/"
    "Electric_Service_Territories/FeatureServer/0/query"
)

# zone -> name and EIA utility numbers
ZONES = {
    "DOM": {"name": "Dominion", "utilities": {19876: "Virginia Electric & Power Co"}},
    "JC": {
        "name": "Jersey Central Power & Light",
        "utilities": {9726: "Jersey Central Power & Lt Co"},
    },
    "AEP": {
        "name": "American Electric Power",
        "utilities": {
            733: "Appalachian Power Co",
            9324: "Indiana Michigan Power Co",
            14006: "Ohio Power Co",
            22053: "Kentucky Power Co",
            10331: "Kingsport Power Co",
            20521: "Wheeling Power Co",
        },
    },
    "AE": {"name": "Atlantic City Electric", "utilities": {963: "Atlantic City Electric Co"}},
}
STATES = {19876: {"VA", "NC"}}  # Dominion's 2025 list adds two WV counties; no retail there
NOT_PJM = {"51520"}  # Bristol, VA: Bristol Virginia Utilities, BA code TVA in EIA-861 2025
MIN_SHARE = 0.02
GRID = 40  # sample points per side of a county's bounding box

MAP_STATES = {
    "34": "NJ", "42": "PA", "24": "MD", "10": "DE", "11": "DC", "51": "VA", "54": "WV",
    "39": "OH", "18": "IN", "26": "MI", "21": "KY", "47": "TN", "37": "NC",
}  # fmt: skip
EXPECT = {
    "51770": "AEP", "51161": "AEP", "34001": "AE", "34009": "AE",
    "51059": "DOM", "51107": "DOM", "34025": "JC", "34029": "JC",
}  # fmt: skip
XLSX_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
HEADER = ["Data Year", "Utility Number", "Utility Name", "Short Form", "State", "County"]
OUT = Path(__file__).resolve().parents[2] / "dashboard" / "zones.js"


def fetch(url, path, params=None):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, params=params, timeout=180, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        path.write_bytes(r.content)
    return path


def read_service_territory(zip_path):
    """Rows (utility number, state, county) from the Service Territory sheet. No openpyxl."""
    with zipfile.ZipFile(zip_path) as outer:
        book = outer.read(f"Service_Territory_{YEAR}.xlsx")
    with zipfile.ZipFile(io.BytesIO(book)) as z:
        strings = [
            "".join(t.text or "" for t in si.iter(XLSX_NS + "t"))
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall(XLSX_NS + "si")
        ]
        sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    rows = []
    for row in sheet.iter(XLSX_NS + "row"):
        cells = {}
        for c in row.findall(XLSX_NS + "c"):
            v = c.find(XLSX_NS + "v")
            if v is not None:
                col = re.match(r"[A-Z]+", c.get("r")).group()
                cells[col] = strings[int(v.text)] if c.get("t") == "s" else v.text
        rows.append([cells.get(k, "") for k in "ABCDEF"])
    if rows[0] != HEADER:
        raise SystemExit(f"unexpected Service Territory header: {rows[0]}")
    return [(int(r[1]), r[4], r[5]) for r in rows[1:] if r[1].isdigit()]


def norm(name):
    return re.sub(r"[^a-z]", "", name.lower())


def county_lookup(topo):
    """Function (state abbreviation, EIA county name) -> FIPS or None."""
    by_name = {}
    for g in topo["objects"]["counties"]["geometries"]:
        st = MAP_STATES.get(g["id"][:2])
        if st:
            by_name.setdefault((st, norm(g["properties"]["name"])), []).append(g["id"])

    def find(state, county):
        ids = sorted(by_name.get((state, norm(county)), []))
        if ids:  # a Virginia county and city can share a name; the plain name is the county
            return ids[0]
        if state == "VA" and norm(county).endswith("city"):
            ids = [i for i in by_name.get((state, norm(county)[:-4]), []) if i >= "51500"]
            if ids:
                return ids[0]
        return None

    return find


def county_rings(topo, geom):
    """Polygon rings of one county as arrays of absolute coordinates."""
    scale, translate = topo["transform"]["scale"], topo["transform"]["translate"]

    def arc(i):
        pts = np.cumsum(np.array(topo["arcs"][i if i >= 0 else ~i], dtype=float), axis=0)
        pts = pts * scale + translate
        return pts if i >= 0 else pts[::-1]

    polys = geom["arcs"] if geom["type"] == "MultiPolygon" else [geom["arcs"]]
    return [np.vstack([arc(i) for i in ring]) for poly in polys for ring in poly]


def inside(points, rings):
    """Even-odd point-in-polygon test of many points against many rings."""
    hit = np.zeros(len(points), dtype=bool)
    x, y = points[:, 0], points[:, 1]
    for ring in rings:
        lo, hi = ring.min(axis=0), ring.max(axis=0)
        near = (x >= lo[0]) & (x <= hi[0]) & (y >= lo[1]) & (y <= hi[1])
        if not near.any():
            continue
        px, py = x[near][:, None], y[near][:, None]
        x1, y1 = ring[:-1, 0], ring[:-1, 1]
        x2, y2 = ring[1:, 0], ring[1:, 1]
        with np.errstate(divide="ignore", invalid="ignore"):
            cross = ((y1 > py) != (y2 > py)) & (px < (x2 - x1) * (py - y1) / (y2 - y1) + x1)
        hit[near] ^= cross.sum(axis=1) % 2 == 1
    return hit


def area_shares(scratch, fips_list, utilities):
    """Share of each county's area inside each utility's polygon: {fips: {utility: share}}."""
    path = fetch(ATLAS_URL.format(name="counties-10m.json"), scratch / "atlas/counties-10m.json")
    topo = json.loads(path.read_text())
    geoms = {g["id"]: g for g in topo["objects"]["counties"]["geometries"]}
    polygons = {}
    for uid in utilities:
        params = {"where": f"id='{uid}'", "outFields": "id,name,year", "outSR": 4326}
        params["f"] = "geojson"
        gj = json.loads(fetch(HIFLD_URL, scratch / f"hifld/{uid}.geojson", params).read_text())
        if not gj.get("features"):
            raise SystemExit(f"no service territory polygon for utility {uid}")
        polygons[uid] = []
        for f in gj["features"]:
            g = f["geometry"]
            for poly in g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]:
                polygons[uid] += [np.array(r, dtype=float)[:, :2] for r in poly]
    shares = {}
    for fips in fips_list:
        rings = county_rings(topo, geoms[fips])
        lo = np.min([r.min(axis=0) for r in rings], axis=0)
        hi = np.max([r.max(axis=0) for r in rings], axis=0)
        gx, gy = np.meshgrid(*(np.linspace(lo[k], hi[k], GRID + 2)[1:-1] for k in (0, 1)))
        pts = np.column_stack([gx.ravel(), gy.ravel()])
        pts = pts[inside(pts, rings)]
        shares[fips] = {
            u: float(inside(pts, polygons[u]).mean()) if len(pts) else 0.0 for u in utilities
        }
    return shares


def neighbours(topo):
    """{fips: set of fips sharing a boundary arc}."""
    owners = {}
    for g in topo["objects"]["counties"]["geometries"]:
        polys = g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]]
        for i in {a if a >= 0 else ~a for poly in polys for ring in poly for a in ring}:
            owners.setdefault(i, set()).add(g["id"])
    near = {}
    for ids in owners.values():
        for a in ids:
            near.setdefault(a, set()).update(ids - {a})
    return near


def cut_topology(topo):
    """Keep the counties of MAP_STATES and only the arcs they use."""
    index = {}

    def remap(a):
        j = index.setdefault(a if a >= 0 else ~a, len(index))
        return j if a >= 0 else ~j

    geoms = []
    for g in topo["objects"]["counties"]["geometries"]:
        if g["id"][:2] not in MAP_STATES:
            continue
        if g["type"] == "MultiPolygon":
            arcs = [[[remap(a) for a in ring] for ring in poly] for poly in g["arcs"]]
        else:
            arcs = [[remap(a) for a in ring] for ring in g["arcs"]]
        name = {"name": g["properties"]["name"]}
        geoms.append({"type": g["type"], "arcs": arcs, "id": g["id"], "properties": name})
    return {
        "type": "Topology",
        "bbox": topo["bbox"],
        "transform": topo["transform"],
        "objects": {"counties": {"type": "GeometryCollection", "geometries": geoms}},
        "arcs": [topo["arcs"][i] for i in index],  # insertion order is the new numbering
    }


def assign(scratch, topo, rows):
    """Apply the three rules. Returns (assigned, shared, filled) and prints the record."""
    names = {g["id"]: g["properties"]["name"] for g in topo["objects"]["counties"]["geometries"]}
    zone_of = {u: z for z, spec in ZONES.items() for u in spec["utilities"]}
    find = county_lookup(topo)

    def label(fips):
        return f"{fips} {names[fips]}, {MAP_STATES[fips[:2]]}"

    # rule 1: counties each zone's utilities list
    listed = {}
    for uid, state, county in rows:
        if uid not in zone_of or state not in STATES.get(uid, MAP_STATES.values()):
            continue
        fips = find(state, county)
        if fips is None:
            print(f"no county match: utility {uid}, {state}, {county!r}")
            continue
        listed.setdefault(fips, set()).add(uid)

    # rule 2: polygons remove strays and settle double claims
    cities = [f for f in sorted(names) if "51500" <= f < "52000"]
    shares = area_shares(scratch, sorted(set(listed) | set(cities)), sorted(zone_of))

    mapped = {(u, f[:2]) for f, us in listed.items() for u in us if shares[f][u] >= MIN_SHARE}
    for u, st in sorted({(u, f[:2]) for f, us in listed.items() for u in us} - mapped):
        print(f"no polygon for utility {u} in {MAP_STATES[st]}: its list is kept untested")

    def zone_shares(fips, utilities):
        best = {}
        for u in utilities:
            share = shares[fips][u] if (u, fips[:2]) in mapped else 1.0
            best[zone_of[u]] = max(best.get(zone_of[u], 0.0), share)
        return best

    assigned, shared, dropped, thin = {}, {}, [], []
    for fips, utilities in sorted(listed.items()):
        share = zone_shares(fips, utilities)
        stray = {z: s for z, s in sorted(share.items()) if s < MIN_SHARE}
        dropped += [f"{z} {label(fips)} ({s:.3f})" for z, s in stray.items()]
        live = {z: round(s, 2) for z, s in sorted(share.items()) if s >= MIN_SHARE}
        if not live:
            continue
        assigned[fips] = max(live, key=live.get)
        if len(live) > 1:
            shared[fips] = live
        elif live[assigned[fips]] < 0.5:
            thin.append(f"{assigned[fips]} {label(fips)} ({live[assigned[fips]]:.2f})")

    # rule 3: Virginia independent cities left without a zone
    near = neighbours(topo)
    filled = {}
    for fips in cities:
        if fips in assigned or fips in NOT_PJM:
            continue
        share = zone_shares(fips, [u for u in zone_of if (u, fips[:2]) in mapped])
        zone = max(sorted(share), key=share.get)
        around = {assigned.get(n) for n in near.get(fips, ()) if n not in cities}
        if share[zone] >= 0.5:
            filled[fips] = (zone, f"polygon {share[zone]:.2f}")
        elif len(around) == 1 and None not in around:
            filled[fips] = (around.pop(), "neighbours")
    assigned.update({f: z for f, (z, _) in filled.items()})

    print("claimed by two zones (share of the county's area in each zone's polygon):")
    for fips, live in shared.items():
        print(f"  {label(fips)}: {live} -> {assigned[fips]}")
    print(f"\ndropped as strays (polygon covers under {MIN_SHARE:.0%} of the county):")
    print("  " + "\n  ".join(dropped))
    print("\nVirginia cities filled:")
    for fips, (zone, why) in filled.items():
        print(f"  {label(fips)} -> {zone} ({why})")
    print("  none: " + ", ".join(f"{names[f]} {f}" for f in cities if f not in assigned))
    print("\nkept, though the polygon covers under half of the county:")
    print("  " + "\n  ".join(thin))
    print("\nchecks:")
    for fips, zone in EXPECT.items():
        got = assigned.get(fips)
        print(f"  {label(fips)}: {got} {'ok' if got == zone else 'EXPECTED ' + zone}")
    return assigned, shared, filled


def main(scratch):
    eia = fetch(EIA_URL, scratch / "eia" / f"f861{YEAR}.zip")
    name = "counties-albers-10m.json"
    atlas = fetch(ATLAS_URL.format(name=name), scratch / "atlas" / name)
    topo = json.loads(atlas.read_text())
    assigned, shared, filled = assign(scratch, topo, read_service_territory(eia))

    zones = {}
    print()
    for zone, spec in ZONES.items():
        fips = sorted(f for f, z in assigned.items() if z == zone)
        zones[zone] = {
            "name": spec["name"],
            "utilities": [f"{n} (EIA {u})" for u, n in spec["utilities"].items()],
            "fips": fips,
            "shared": sorted(f for f in shared if zone in shared[f]),
            "filled": sorted(f for f, (z, _) in filled.items() if z == zone),
        }
        by_state = {}
        for f in fips:
            by_state[MAP_STATES[f[:2]]] = by_state.get(MAP_STATES[f[:2]], 0) + 1
        print(f"{zone}: {len(fips)} counties {by_state}")

    small = cut_topology(topo)
    body = (
        f"// Built by tools/zone_selection/build_zone_map.py from the EIA-861 {YEAR} Service\n"
        "// Territory file and us-atlas@3 counties-albers-10m. Do not edit by hand.\n"
        "// See notes/zone_geography.md.\n"
        f"window.ZONES = {json.dumps(zones, separators=(',', ':'))};\n"
        f"window.COUNTIES = {json.dumps(small, separators=(',', ':'))};\n"
    )
    OUT.write_text(body)
    n = len(small["objects"]["counties"]["geometries"])
    print(f"\nwrote dashboard/{OUT.name}: {len(body) / 1024:.0f} KB, {n} counties")
    for p in [eia, atlas, *sorted((scratch / "hifld").glob("*.geojson"))]:
        print(f"  sha256 {hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]))
