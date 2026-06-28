#!/usr/bin/env python3
"""
WildGuard M8 — Daily poaching-risk model + unpredictable patrol route planner.

Poachers study ranger patterns. Always patrolling the same route at the same time = poachers
just wait. This script scores every grid cell in a reserve for poaching risk (next 7 days),
then plans a patrol route that hits the high-risk cells first while keeping a random component
so no pattern is detectable.

Design goals (see dev.md):
    - Runs offline on a Raspberry Pi. numpy only — no sklearn, no ephem, no internet.
    - Interpretable score: a weighted logistic blend of features a ranger can reason about.
    - Works with ZERO setup: with no event database it generates a synthetic reserve so you
      can see the full output today, then swap in real data.

Features per (grid_cell, day), all normalized 0..1:
    incident_rate     historical incidents in/near cell (last 90 days), distance-weighted
    days_since_patrol staleness — un-patrolled high-value ground is opportunity
    dist_to_edge      proximity to reserve boundary / access roads (entry points)
    lunar_risk        moon phase; risk peaks ~3 days before full moon (PAWS empirical finding)
    animal_density    prey/target presence in cell (from M5 collar data, optional)

Risk = sigmoid( w . features ).  Weights are exposed below — tune them to your reserve, or
replace compute_risk() with a trained model once you have >6 months of labelled history.

Input
-----
Tactical Events JSON array (hub `GET /events` output, or a file). Each event needs at least:
    {"timestamp": <unix s>, "coordinates": {"latitude":.., "longitude":..},
     "source_type": "...", "threat_class": "..."}
Events with source_type "ranger_report"/"patrol" mark patrol coverage; everything else with a
threat_class (poacher, snare, gunshot, ...) counts as a poaching incident.

Run
---
    python risk_model.py --demo                  # synthetic reserve, no data needed
    python risk_model.py --events events.json    # real hub export
    cat events.json | python risk_model.py
    python risk_model.py --demo --geojson risk.geojson --route route.json --rangers 4

Output
------
    risk.geojson   FeatureCollection, one polygon per cell, properties.risk_score + top_features
    route.json     one waypoint list per ranger (70% high-risk weighted, 30% random)
    stdout         plain-text daily patrol briefing (top zones + per-ranger assignment)
"""
import argparse
import json
import math
import random
import sys
import time

# ---- tunable feature weights (log-odds contribution; raise to weight a feature more) ----
WEIGHTS = {
    "incident_rate":     2.6,
    "days_since_patrol": 0.9,
    "dist_to_edge":      1.1,
    "lunar_risk":        0.7,
    "animal_density":    1.0,
}
BIAS = -2.2  # base log-odds: most cells are low risk on any given day
FEATURE_COLS = list(WEIGHTS.keys())

INCIDENT_HALFLIFE_DAYS = 45.0   # older incidents decay
INCIDENT_RADIUS_M = 1500.0      # an incident raises risk in cells within this radius
PATROL_SOURCES = {"ranger_report", "patrol"}


# --------------------------------------------------------------------------- geo helpers
def meters_per_deg(lat0):
    """Local meters-per-degree (lat, lon) on a sphere around lat0."""
    m_lat = 111_320.0
    m_lon = 111_320.0 * math.cos(math.radians(lat0))
    return m_lat, m_lon


def haversine_m(lat1, lon1, lat2, lon2):
    R = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def sigmoid(x):
    if x < -60:
        return 0.0
    if x > 60:
        return 1.0
    return 1.0 / (1.0 + math.exp(-x))


# --------------------------------------------------------------------------- lunar phase
def lunar_risk_multiplier(when_unix):
    """Moon illumination 0..1 from a known new moon, mapped to a risk factor.

    Empirical (PAWS): poaching risk peaks ~3 days before full moon — enough light to move,
    enough cover before full brightness. No ephem dependency; synodic-month approximation.
    """
    SYNODIC = 29.530588853 * 86400.0
    KNOWN_NEW_MOON = 1704883200.0  # 2024-01-10 12:00 UTC, near a new moon
    age = ((when_unix - KNOWN_NEW_MOON) % SYNODIC) / SYNODIC  # 0=new .. 0.5=full .. 1=new
    illum = (1 - math.cos(2 * math.pi * age)) / 2            # 0..1 illumination
    # shift peak to ~3 days before full (full == age 0.5)
    peak = 0.5 - 3 * 86400.0 / SYNODIC
    closeness = 1 - min(abs(age - peak), 1 - abs(age - peak)) * 2
    return max(0.0, 0.6 * illum + 0.4 * closeness)


# --------------------------------------------------------------------------- grid
class Cell:
    __slots__ = ("cid", "lat", "lon", "feat", "risk")

    def __init__(self, cid, lat, lon):
        self.cid = cid
        self.lat = lat
        self.lon = lon
        self.feat = {k: 0.0 for k in FEATURE_COLS}
        self.risk = 0.0


def build_grid(bbox, cell_m=500.0):
    """Grid covering bbox=(min_lat,min_lon,max_lat,max_lon) at cell_m resolution."""
    min_lat, min_lon, max_lat, max_lon = bbox
    lat0 = (min_lat + max_lat) / 2
    m_lat, m_lon = meters_per_deg(lat0)
    dlat = cell_m / m_lat
    dlon = cell_m / m_lon
    cells = []
    nlat = max(1, int((max_lat - min_lat) / dlat))
    nlon = max(1, int((max_lon - min_lon) / dlon))
    for i in range(nlat):
        for j in range(nlon):
            lat = min_lat + (i + 0.5) * dlat
            lon = min_lon + (j + 0.5) * dlon
            cells.append(Cell(f"c{i:03d}_{j:03d}", lat, lon))
    return cells, (dlat, dlon)


def bbox_of(points, pad_deg=0.01):
    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    return (min(lats) - pad_deg, min(lons) - pad_deg,
            max(lats) + pad_deg, max(lons) + pad_deg)


# --------------------------------------------------------------------------- features
def normalize(vals):
    lo, hi = min(vals), max(vals)
    if hi - lo < 1e-9:
        return [0.0 for _ in vals]
    return [(v - lo) / (hi - lo) for v in vals]


def compute_features(cells, incidents, patrols, now_unix, bbox):
    min_lat, min_lon, max_lat, max_lon = bbox
    cx, cy = (min_lat + max_lat) / 2, (min_lon + max_lon) / 2

    inc_raw, stale_raw, edge_raw = [], [], []
    for c in cells:
        # incident_rate: time-decayed, distance-weighted incident pressure
        s = 0.0
        for (ilat, ilon, its) in incidents:
            d = haversine_m(c.lat, c.lon, ilat, ilon)
            if d > INCIDENT_RADIUS_M:
                continue
            age_days = max(0.0, (now_unix - its) / 86400.0)
            decay = 0.5 ** (age_days / INCIDENT_HALFLIFE_DAYS)
            s += decay * (1 - d / INCIDENT_RADIUS_M)
        inc_raw.append(s)

        # days_since_patrol: time since nearest patrol fix touched this cell
        last = None
        for (plat, plon, pts) in patrols:
            if haversine_m(c.lat, c.lon, plat, plon) <= INCIDENT_RADIUS_M:
                last = pts if last is None else max(last, pts)
        stale_raw.append(90.0 if last is None else min(90.0, (now_unix - last) / 86400.0))

        # dist_to_edge: closer to boundary/access = higher entry risk → invert distance
        edge = min(haversine_m(c.lat, c.lon, min_lat, c.lon),
                   haversine_m(c.lat, c.lon, max_lat, c.lon),
                   haversine_m(c.lat, c.lon, c.lat, min_lon),
                   haversine_m(c.lat, c.lon, c.lat, max_lon))
        edge_raw.append(edge)

    inc_n = normalize(inc_raw)
    stale_n = normalize(stale_raw)
    edge_n = normalize(edge_raw)
    lunar = lunar_risk_multiplier(now_unix)

    for idx, c in enumerate(cells):
        c.feat["incident_rate"] = inc_n[idx]
        c.feat["days_since_patrol"] = stale_n[idx]
        c.feat["dist_to_edge"] = 1.0 - edge_n[idx]   # near edge → high
        c.feat["lunar_risk"] = lunar                  # global, same per day
        c.feat["animal_density"] = c.feat.get("animal_density", 0.0)  # set by M5 if available


def compute_risk(cells):
    for c in cells:
        z = BIAS + sum(WEIGHTS[k] * c.feat[k] for k in FEATURE_COLS)
        c.risk = sigmoid(z)


def top_features(c, n=2):
    contrib = {k: WEIGHTS[k] * c.feat[k] for k in FEATURE_COLS}
    return [k for k, _ in sorted(contrib.items(), key=lambda kv: -kv[1])[:n]]


# --------------------------------------------------------------------------- patrol routing
def weighted_sample(cells, k, rng):
    """Sample k distinct cells with probability proportional to risk (no replacement)."""
    pool = list(cells)
    chosen = []
    for _ in range(min(k, len(pool))):
        total = sum(c.risk for c in pool) or 1.0
        r = rng.random() * total
        acc = 0.0
        for i, c in enumerate(pool):
            acc += c.risk
            if acc >= r:
                chosen.append(pool.pop(i))
                break
    return chosen


def greedy_route(start, waypoints):
    """Nearest-neighbour ordering from start over waypoints (cheap field TSP)."""
    route = []
    cur = start
    remaining = list(waypoints)
    while remaining:
        nxt = min(remaining, key=lambda c: haversine_m(cur[0], cur[1], c.lat, c.lon))
        route.append(nxt)
        cur = (nxt.lat, nxt.lon)
        remaining.remove(nxt)
    return route


def plan_routes(cells, n_rangers, waypoints_each, ranger_starts, seed=None):
    """70% waypoints drawn from top-40% risk cells (risk-weighted), 30% pure random.

    The random component is the point: it makes the patrol unpredictable so poachers can't
    learn the schedule. Tune the split with --random-frac.
    """
    rng = random.Random(seed if seed is not None else time.time())
    ranked = sorted(cells, key=lambda c: -c.risk)
    top = ranked[:max(1, int(len(ranked) * 0.4))]
    rest = ranked[max(1, int(len(ranked) * 0.4)):] or ranked

    routes = []
    for r in range(n_rangers):
        n_hot = max(1, round(waypoints_each * 0.7))
        n_rand = max(0, waypoints_each - n_hot)
        wp = weighted_sample(top, n_hot, rng) + rng.sample(rest, min(n_rand, len(rest)))
        start = ranger_starts[r] if ranger_starts else (top[0].lat, top[0].lon)
        routes.append(greedy_route(start, wp))
    return routes


# --------------------------------------------------------------------------- IO
def load_events(args):
    if args.events:
        with open(args.events) as f:
            return json.load(f)
    if not sys.stdin.isatty():
        data = sys.stdin.read().strip()
        if data:
            return json.loads(data)
    return None


def split_events(events):
    incidents, patrols, pts = [], [], []
    for e in events:
        c = e.get("coordinates", {})
        lat, lon = c.get("latitude"), c.get("longitude")
        ts = e.get("timestamp")
        if lat is None or lon is None or ts is None:
            continue
        pts.append((lat, lon))
        if e.get("source_type") in PATROL_SOURCES:
            patrols.append((lat, lon, ts))
        elif e.get("threat_class"):
            incidents.append((lat, lon, ts))
    return incidents, patrols, pts


def synth_reserve(now_unix, seed=7):
    """Generate a plausible reserve: a hotspot near one edge + scattered patrols."""
    rng = random.Random(seed)
    base_lat, base_lon = -2.35, 34.82
    bbox = (base_lat, base_lon, base_lat + 0.06, base_lon + 0.06)  # ~6.6 km square
    incidents, patrols, pts = [], [], []
    hot = (base_lat + 0.012, base_lon + 0.010)  # near SW edge = access road
    for _ in range(40):
        lat = hot[0] + rng.gauss(0, 0.006)
        lon = hot[1] + rng.gauss(0, 0.006)
        ts = now_unix - rng.randint(0, 90) * 86400
        incidents.append((lat, lon, ts)); pts.append((lat, lon))
    for _ in range(25):  # patrols cluster in the (safe) centre — the realistic bias
        lat = base_lat + 0.03 + rng.gauss(0, 0.008)
        lon = base_lon + 0.03 + rng.gauss(0, 0.008)
        ts = now_unix - rng.randint(0, 14) * 86400
        patrols.append((lat, lon, ts)); pts.append((lat, lon))
    return bbox, incidents, patrols, pts


def cells_to_geojson(cells, step):
    dlat, dlon = step
    feats = []
    for c in cells:
        hy, hx = dlat / 2, dlon / 2
        ring = [[c.lon - hx, c.lat - hy], [c.lon + hx, c.lat - hy],
                [c.lon + hx, c.lat + hy], [c.lon - hx, c.lat + hy],
                [c.lon - hx, c.lat - hy]]
        feats.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [ring]},
            "properties": {
                "cell_id": c.cid,
                "risk_score": round(c.risk, 4),
                "top_features": top_features(c),
            },
        })
    return {"type": "FeatureCollection", "features": feats}


def routes_to_json(routes):
    return {
        "generated_at": int(time.time()),
        "rangers": [
            {"ranger": i + 1,
             "waypoints": [{"cell_id": c.cid, "lat": round(c.lat, 6),
                            "lon": round(c.lon, 6), "risk_score": round(c.risk, 4)}
                           for c in route]}
            for i, route in enumerate(routes)
        ],
    }


def print_briefing(cells, routes, now_unix):
    ranked = sorted(cells, key=lambda c: -c.risk)
    print("=" * 64)
    print(f"DAILY PATROL BRIEFING — {time.strftime('%Y-%m-%d', time.gmtime(now_unix))} UTC")
    print(f"Lunar risk factor: {lunar_risk_multiplier(now_unix):.2f}")
    print("=" * 64)
    print("\nTOP 5 RISK ZONES:")
    for c in ranked[:5]:
        why = ", ".join(top_features(c))
        print(f"  {c.cid}  risk={c.risk:.2f}  ({c.lat:.4f},{c.lon:.4f})  why: {why}")
    print("\nPATROL ASSIGNMENT (70% high-risk / 30% random — keep poachers guessing):")
    for i, route in enumerate(routes):
        chain = " -> ".join(c.cid for c in route)
        avg = sum(c.risk for c in route) / len(route) if route else 0
        print(f"  Ranger {i + 1} (avg risk {avg:.2f}): {chain}")
    print("\nNote: random waypoints are intentional. Do not 'optimise them away'.")


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="WildGuard M8 risk model + patrol planner")
    ap.add_argument("--events", help="Tactical Events JSON file (hub /events export)")
    ap.add_argument("--demo", action="store_true", help="run on a synthetic reserve")
    ap.add_argument("--cell-m", type=float, default=500.0, help="grid cell size in meters")
    ap.add_argument("--rangers", type=int, default=4)
    ap.add_argument("--waypoints", type=int, default=8, help="waypoints per ranger")
    ap.add_argument("--geojson", help="write risk FeatureCollection here")
    ap.add_argument("--route", help="write patrol routes JSON here")
    ap.add_argument("--seed", type=int, help="fix randomness (testing only — NOT in the field)")
    args = ap.parse_args()

    now = int(time.time())
    events = load_events(args)

    if events is None and not args.demo:
        print("No events on stdin/--events. Use --demo for a synthetic run, or pipe hub /events.",
              file=sys.stderr)
        return 2

    if args.demo or events is None:
        bbox, incidents, patrols, pts = synth_reserve(now)
        print("[demo] synthetic reserve: 40 incidents (edge hotspot), 25 patrols (centre bias)\n",
              file=sys.stderr)
    else:
        incidents, patrols, pts = split_events(events)
        if not pts:
            print("No usable coordinates in events.", file=sys.stderr)
            return 2
        bbox = bbox_of(pts)

    cells, step = build_grid(bbox, args.cell_m)
    compute_features(cells, incidents, patrols, now, bbox)
    compute_risk(cells)
    routes = plan_routes(cells, args.rangers, args.waypoints, None, seed=args.seed)

    if args.geojson:
        with open(args.geojson, "w") as f:
            json.dump(cells_to_geojson(cells, step), f, indent=2)
        print(f"[ok] risk GeoJSON -> {args.geojson} ({len(cells)} cells)", file=sys.stderr)
    if args.route:
        with open(args.route, "w") as f:
            json.dump(routes_to_json(routes), f, indent=2)
        print(f"[ok] patrol routes -> {args.route}", file=sys.stderr)

    print_briefing(cells, routes, now)
    return 0


if __name__ == "__main__":
    sys.exit(main())
