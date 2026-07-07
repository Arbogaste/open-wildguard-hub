"""
Regression tests for M3 TDoA localization (toolkit/python/tdoa_locate.py).

History: the original linearization had a sign error in b that put the fix ~6.5 km off with
perfect input, and the pure-linear solve was underdetermined with exactly 3 nodes. These tests
pin the fixed behaviour: sub-100 m accuracy on park-scale geometry, 3 nodes minimum, stdlib only.
"""
import json
import math
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(HERE, "..", "python")
sys.path.insert(0, PY)

import tdoa_locate as T  # noqa: E402

GEO4 = [(-2.312, 34.821), (-2.385, 34.851), (-2.348, 34.789), (-2.300, 34.860)]
SRC = (-2.340, 34.830)
C = 343.0


def make_nodes(src, nodes_geo, noise_ms=0.0, seed=1):
    """Synthesize exact (optionally clock-noisy) arrival times from a ground-truth source."""
    rng = random.Random(seed)
    lat0, lon0 = nodes_geo[0]
    sx, sy = T.geo_to_enu(src[0], src[1], lat0, lon0)
    out = []
    for i, (la, lo) in enumerate(nodes_geo):
        ax, ay = T.geo_to_enu(la, lo, lat0, lon0)
        t = 1782046800.0 + math.hypot(ax - sx, ay - sy) / C + rng.gauss(0, noise_ms / 1000)
        out.append({"id": f"n{i}", "lat": la, "lon": lo, "t": t})
    return out


def err_m(est):
    ref = GEO4[0]
    sx, sy = T.geo_to_enu(SRC[0], SRC[1], ref[0], ref[1])
    ex, ey = T.geo_to_enu(est[0], est[1], ref[0], ref[1])
    return math.hypot(ex - sx, ey - sy)


def test_four_nodes_exact_times():
    lat, lon, rms = T.localize(make_nodes(SRC, GEO4), C)
    assert err_m((lat, lon)) < 1.0 and rms < 1.0


def test_three_nodes_exact_times():
    # 3 nodes = 2 equations: linear form is underdetermined, Gauss-Newton must still solve it
    lat, lon, _ = T.localize(make_nodes(SRC, GEO4[:3]), C)
    assert err_m((lat, lon)) < 1.0


def test_clock_noise_2ms_stays_useful():
    # 2 ms sync error ≈ 0.7 m of range error — the fix must stay well inside dispatch range
    lat, lon, _ = T.localize(make_nodes(SRC, GEO4, noise_ms=2), C)
    assert err_m((lat, lon)) < 100.0


def test_residual_flags_garbage_input():
    # one node reporting a wildly wrong time must show up as a large residual
    nodes = make_nodes(SRC, GEO4)
    nodes[2]["t"] += 5.0  # 5 s off = ~1.7 km of phantom range
    _, _, rms = T.localize(nodes, C)
    assert rms > 100.0, "bad sync must be visible in residual_rms_m"


def test_cli_stdin_json():
    inp = json.dumps({"speed_of_sound": C, "nodes": make_nodes(SRC, GEO4, noise_ms=1)})
    r = subprocess.run([sys.executable, os.path.join(PY, "tdoa_locate.py")],
                       input=inp, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert err_m((out["source"]["latitude"], out["source"]["longitude"])) < 100.0
    assert "residual_rms_m" in out


def test_rejects_fewer_than_three_nodes():
    inp = json.dumps({"nodes": make_nodes(SRC, GEO4[:2])})
    r = subprocess.run([sys.executable, os.path.join(PY, "tdoa_locate.py")],
                       input=inp, capture_output=True, text=True)
    assert r.returncode != 0


def test_no_numpy_needed():
    # field Pis clone and run with zero pip installs — keep it that way
    src = open(os.path.join(PY, "tdoa_locate.py")).read()
    assert "import numpy" not in src
