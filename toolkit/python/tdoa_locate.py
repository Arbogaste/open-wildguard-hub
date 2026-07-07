#!/usr/bin/env python3
"""
WildGuard M3 — TDoA sound-source localization. Given >=3 time-synced acoustic nodes that each
report the arrival time of the same event (gunshot), solve for the source coordinates.

Method: least-squares on time-difference-of-arrival, local ENU plane (good for park-scale areas).
Offline, stdlib only — no numpy. Output includes residual_rms_m: large residual = bad node
clock sync or wrong node coordinates; treat the fix as suspect.

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
import time
import uuid


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


def solve_lstsq(A, b):
    """Least-squares solve of A·x = b via normal equations (AᵀA)x = Aᵀb.
    Stdlib only — the system is tiny (3 unknowns), no numpy needed on a field Pi.
    Gaussian elimination with partial pivoting."""
    n = len(A[0])
    M = [[sum(A[k][i] * A[k][j] for k in range(len(A))) for j in range(n)] for i in range(n)]
    v = [sum(A[k][i] * b[k] for k in range(len(A))) for i in range(n)]
    for col in range(n):  # forward elimination
        piv = max(range(col, n), key=lambda r: abs(M[r][col]))
        if abs(M[piv][col]) < 1e-12:
            sys.exit("Degenerate node geometry (nodes collinear?) — cannot solve.")
        M[col], M[piv] = M[piv], M[col]
        v[col], v[piv] = v[piv], v[col]
        for r in range(col + 1, n):
            f = M[r][col] / M[col][col]
            for j in range(col, n):
                M[r][j] -= f * M[col][j]
            v[r] -= f * v[col]
    x = [0.0] * n  # back substitution
    for i in range(n - 1, -1, -1):
        x[i] = (v[i] - sum(M[i][j] * x[j] for j in range(i + 1, n))) / M[i][i]
    return x


def localize(nodes, c):
    """Returns (lat, lon, residual_rms_m). residual_rms_m ≈ how well the solution
    explains the arrival times — large value = bad sync / wrong node position."""
    lat0, lon0 = nodes[0]["lat"], nodes[0]["lon"]
    pts = [geo_to_enu(n["lat"], n["lon"], lat0, lon0) for n in nodes]
    t = [n["t"] for n in nodes]
    ref = int(min(range(len(t)), key=lambda i: t[i]))  # earliest = reference
    xr, yr = pts[ref]

    # Linearized TDoA (Fang style). Unknowns [x, y, R] with R = distance source→ref node.
    # From ||pi−s|| = R + di:  2(pi−pr)·s + 2·di·R = ||pi||² − ||pr||² − di²
    A, b = [], []
    for i, (xi, yi) in enumerate(pts):
        if i == ref:
            continue
        di = c * (t[i] - t[ref])  # range difference (distance_i − distance_ref)
        A.append([2 * (xi - xr), 2 * (yi - yr), 2 * di])
        b.append((xi**2 + yi**2) - (xr**2 + yr**2) - di**2)
    if len(A) >= 3:  # 4+ nodes: linear solve gives a good starting point
        x, y, _R = solve_lstsq(A, b)
    else:            # exactly 3 nodes: linear system is underdetermined — start at centroid
        x = sum(p[0] for p in pts) / len(pts)
        y = sum(p[1] for p in pts) / len(pts)

    # Gauss-Newton refinement on the true nonlinear TDoA equations. Unknowns (x, y) only,
    # so 3 nodes (2 equations) already determine the fix. A few iterations converge.
    for _ in range(50):
        J, r = [], []
        dr = math.hypot(x - xr, y - yr) or 1e-9
        for i, (xi, yi) in enumerate(pts):
            if i == ref:
                continue
            di_est = math.hypot(x - xi, y - yi) or 1e-9
            r.append((di_est - dr) - c * (t[i] - t[ref]))
            J.append([(x - xi) / di_est - (x - xr) / dr,
                      (y - yi) / di_est - (y - yr) / dr])
        try:
            dx, dy = solve_lstsq(J, [-v for v in r])
        except SystemExit:
            break  # singular Jacobian — keep current estimate
        x, y = x + dx, y + dy
        if math.hypot(dx, dy) < 0.01:  # converged to 1 cm
            break

    # residual: predicted vs measured range differences, RMS in meters
    dr = math.hypot(x - xr, y - yr)
    res = []
    for i, (xi, yi) in enumerate(pts):
        if i == ref:
            continue
        res.append((math.hypot(x - xi, y - yi) - dr) - c * (t[i] - t[ref]))
    rms = math.sqrt(sum(r * r for r in res) / len(res))

    lat, lon = enu_to_geo(x, y, lat0, lon0)
    return lat, lon, rms


def make_event(lat, lon, rms, nodes, threat="gunshot"):
    """Localization result → canonical Tactical Event (event_schema.json), so a gunshot fix
    flows into the same pipeline as every other detector. Confidence degrades with the residual:
    a clean solve (rms≈0) is trusted, a noisy/bad-sync one is flagged low."""
    conf = round(1.0 / (1.0 + rms / 50.0), 3)  # rms 0→1.0, 50 m→0.5, 200 m→0.2
    return {
        "event_id": str(uuid.uuid4()),
        "timestamp": int(time.time()),
        "source_type": "acoustic_node",
        "source_id": "+".join(n["id"] for n in nodes),
        "coordinates": {"latitude": round(lat, 6), "longitude": round(lon, 6), "elevation": None},
        "threat_class": threat,
        "confidence": conf,
        "evidence_hash": None, "evidence_url": None,
        "metadata": {"module": "M3", "method": "tdoa", "residual_rms_m": round(rms, 1),
                     "nodes_used": [n["id"] for n in nodes], "node_count": len(nodes)},
    }


# 3 nodes, exact arrival times from a source at (-2.351, 34.819) — runs offline, no network.
DEMO = {"speed_of_sound": 343.0, "nodes": [
    {"id": "aco_01", "lat": -2.312, "lon": 34.821, "t": 1782046800.000},
    {"id": "aco_02", "lat": -2.385, "lon": 34.851, "t": 1782046800.145},
    {"id": "aco_03", "lat": -2.348, "lon": 34.789, "t": 1782046800.117},
]}


def main():
    p = argparse.ArgumentParser(description="WildGuard M3 TDoA gunshot localizer")
    p.add_argument("--file", help="event JSON (default: stdin)")
    p.add_argument("--demo", action="store_true", help="offline sample, 3 synced nodes")
    p.add_argument("--events", help="write the result as a canonical Tactical Event here "
                                    "(feeds wildguard.py / wg_store.py)")
    p.add_argument("--threat", default="gunshot", help="threat_class for the event")
    args = p.parse_args()

    if args.demo:
        data = DEMO
        print("[demo] 3 synced acoustic nodes, synthetic gunshot\n", file=sys.stderr)
    else:
        raw = open(args.file).read() if args.file else sys.stdin.read()
        data = json.loads(raw)
    nodes = data["nodes"]
    if len(nodes) < 3:
        sys.exit("Need >=3 nodes for 2D TDoA.")
    c = float(data.get("speed_of_sound", 343.0))
    lat, lon, rms = localize(nodes, c)
    event = make_event(lat, lon, rms, nodes, args.threat)

    if args.events:
        with open(args.events, "w", encoding="utf-8") as f:
            json.dump([event], f, indent=2, ensure_ascii=False)
        print(f"[ok] event -> {args.events}", file=sys.stderr)
    print(json.dumps({"source": event["coordinates"], "confidence": event["confidence"],
                      "residual_rms_m": round(rms, 1),
                      "nodes_used": [n["id"] for n in nodes]}, indent=2))


if __name__ == "__main__":
    main()
