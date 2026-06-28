#!/usr/bin/env python3
"""
WildGuard M5 — GPS-collar geofence & threat-proximity alerter.

Given collar fix points for tracked animals and a set of zones (protected boundary, danger areas
near roads/villages), raise an alert when an animal leaves the protected area or strays near a known
risk edge — early warning that a collared animal is exposed to poaching.

Offline, stdlib only. Point-in-polygon (ray casting) + great-circle distance. No GIS install.

Input JSON (--file or stdin):
    {
      "protected": [[lat,lon], [lat,lon], ...],          # polygon, protected area boundary
      "danger_edges": [[lat,lon], ...],                  # optional point hazards (roads, snare lines)
      "danger_radius_m": 800,
      "fixes": [
        {"collar_id":"c1","species":"elephant","lat":-2.34,"lon":34.82,"ts":1782046800}
      ]
    }

Run
---
    python gps_geofence.py --demo
    python gps_geofence.py --file fixes.json --events alerts.json

Output: Tactical Events (source_type=gps_collar) for each breach/proximity, + briefing.
"""
import argparse
import json
import math
import sys
import time
import uuid


def haversine_m(a, b):
    R = 6_371_000.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dphi = math.radians(b[0] - a[0])
    dlam = math.radians(b[1] - a[1])
    h = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dlam/2)**2
    return 2 * R * math.asin(math.sqrt(h))


def point_in_poly(pt, poly):
    """Ray casting. poly = [[lat,lon], ...]; uses lon as x, lat as y."""
    x, y = pt[1], pt[0]
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i][1], poly[i][0]
        x2, y2 = poly[(i + 1) % n][1], poly[(i + 1) % n][0]
        if (y1 > y) != (y2 > y):
            xinter = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < xinter:
                inside = not inside
    return inside


def event(fix, threat, conf, note):
    return {
        "event_id": str(uuid.uuid4()),
        "timestamp": int(fix.get("ts", time.time())),
        "source_type": "gps_collar",
        "source_id": fix.get("collar_id", "collar"),
        "coordinates": {"latitude": fix["lat"], "longitude": fix["lon"], "elevation": None},
        "threat_class": threat,
        "confidence": conf,
        "evidence_hash": None, "evidence_url": None,
        "metadata": {"species": fix.get("species"), "note": note, "needs_human_review": True},
    }


DEMO = {
    "protected": [[-2.40, 34.80], [-2.40, 34.88], [-2.30, 34.88], [-2.30, 34.80]],
    "danger_edges": [[-2.41, 34.84]],
    "danger_radius_m": 1500,
    "fixes": [
        {"collar_id": "ele_07", "species": "elephant", "lat": -2.35, "lon": 34.84, "ts": 1782046800},
        {"collar_id": "ele_07", "species": "elephant", "lat": -2.405, "lon": 34.84, "ts": 1782050400},
        {"collar_id": "rhino_2", "species": "rhino", "lat": -2.38, "lon": 34.83, "ts": 1782050400},
    ],
}


def main():
    ap = argparse.ArgumentParser(description="WildGuard M5 collar geofence")
    ap.add_argument("--file")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--events")
    args = ap.parse_args()

    if args.demo:
        data = DEMO
    elif args.file:
        data = json.load(open(args.file, encoding="utf-8"))
    elif not sys.stdin.isatty():
        data = json.loads(sys.stdin.read())
    else:
        print("Need --file, stdin, or --demo.", file=sys.stderr)
        return 2

    poly = data["protected"]
    edges = data.get("danger_edges", [])
    drad = data.get("danger_radius_m", 1000)
    alerts = []
    for fix in data["fixes"]:
        pt = [fix["lat"], fix["lon"]]
        if not point_in_poly(pt, poly):
            alerts.append(event(fix, "geofence_breach", 0.9,
                                "animal outside protected boundary"))
            continue
        for e in edges:
            d = haversine_m(pt, e)
            if d <= drad:
                alerts.append(event(fix, "threat_proximity", 0.7,
                                    f"within {int(d)} m of danger edge"))
                break

    if args.events:
        json.dump(alerts, open(args.events, "w", encoding="utf-8"), indent=2)
        print(f"[ok] {len(alerts)} events -> {args.events}", file=sys.stderr)

    print("=" * 56)
    print(f"COLLAR GEOFENCE — {len(data['fixes'])} fixes, {len(alerts)} alerts")
    print("=" * 56)
    for a in alerts:
        m = a["metadata"]
        print(f"  [{a['threat_class']}] {a['source_id']} ({m['species']}) "
              f"@ {a['coordinates']['latitude']},{a['coordinates']['longitude']} — {m['note']}")
    if not alerts:
        print("  All collared animals inside protected area, clear of danger edges.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
