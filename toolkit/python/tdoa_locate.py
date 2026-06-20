#!/usr/bin/env python3
"""
WildGuard M3 — TDoA sound-source localization. Given >=3 time-synced acoustic nodes that each
report the arrival time of the same event (gunshot), solve for the source coordinates.

Method: least-squares on time-difference-of-arrival, local ENU plane (good for park-scale areas).

Input JSON (stdin or --file):
    {
      "speed_of_sound": 343.0,
      "nodes": [
        {"id":"n1","lat":-2.312,"lon":34.821,"t":1782046800.000},
        {"id":"n2","lat":-2.385,"lon":34.851,"t":1782046800.412},
        {"id":"n3","lat":-2.348,"lon":34.789,"t":1782046800.270}
      ]
    }

Run
---
    python tdoa_locate.py --file event.json
    echo '{...}' | python tdoa_locate.py
"""
import argparse
import json
import math
import sys


def geo_to_enu(lat, lon, lat0, lon0):
    """Approx local East-North meters around (lat0,lon0)."""
    R = 6371000.0
    x = math.radians(lon - lon0) * R * math.cos(math.radians(lat0))
    y = math.radians(lat - lat0) * R
    return x, y


def enu_to_geo(x, y, lat0, lon0):
    R = 6371000.0
    lat = lat0 + math.degrees(y / R)
    lon = lon0 + math.degrees(x / (R * math.cos(math.radians(lat0))))
    return lat, lon


def localize(nodes, c):
    try:
        import numpy as np
    except ImportError:
        sys.exit("Install numpy:  pip install numpy")
    lat0, lon0 = nodes[0]["lat"], nodes[0]["lon"]
    pts = [geo_to_enu(n["lat"], n["lon"], lat0, lon0) for n in nodes]
    t = [n["t"] for n in nodes]
    ref = int(min(range(len(t)), key=lambda i: t[i]))  # earliest = reference
    xr, yr = pts[ref]

    # Linearized TDoA (Fang/− style): each non-ref node gives one equation.
    A, b = [], []
    for i, (xi, yi) in enumerate(pts):
        if i == ref:
            continue
        dt = t[i] - t[ref]
        di = c * dt  # range difference (distance_i - distance_ref)
        A.append([2 * (xi - xr), 2 * (yi - yr), 2 * di])
        b.append(di**2 - (xi**2 - xr**2) - (yi**2 - yr**2))
    A, b = np.array(A), np.array(b)
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    x, y = sol[0], sol[1]
    lat, lon = enu_to_geo(x, y, lat0, lon0)
    return lat, lon


def main():
    p = argparse.ArgumentParser(description="WildGuard M3 TDoA localizer")
    p.add_argument("--file", help="event JSON (default: stdin)")
    args = p.parse_args()
    raw = open(args.file).read() if args.file else sys.stdin.read()
    data = json.loads(raw)
    nodes = data["nodes"]
    if len(nodes) < 3:
        sys.exit("Need >=3 nodes for 2D TDoA.")
    c = float(data.get("speed_of_sound", 343.0))
    lat, lon = localize(nodes, c)
    print(json.dumps({"source": {"latitude": round(lat, 6), "longitude": round(lon, 6)},
                      "nodes_used": [n["id"] for n in nodes]}, indent=2))


if __name__ == "__main__":
    main()
