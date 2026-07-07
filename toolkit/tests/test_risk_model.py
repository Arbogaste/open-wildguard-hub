"""
Tests for M8 risk model + patrol planner (toolkit/python/risk_model.py).

The two properties a ranger's life and time depend on:
  1. risk score is a real probability in [0,1] and higher where incidents cluster;
  2. patrol routes stay UNPREDICTABLE — same input, different routes — because a fixed route
     is a route poachers learn. These tests pin both, plus the lunar factor and stdlib purity.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(HERE, "..", "python")
sys.path.insert(0, PY)

import risk_model as R  # noqa: E402


def _incident(lat, lon, ts=1782046800):
    return {"event_id": f"i{lat}{lon}", "timestamp": ts, "source_type": "camera_trap",
            "coordinates": {"latitude": lat, "longitude": lon},
            "threat_class": "poacher", "confidence": 0.9}


def _grid_over(incident_events, cell_m=500.0, now=1782046800):
    # split_events converts canonical events into the (lat, lon, ts) tuples compute_features wants
    incidents, patrols, pts = R.split_events(incident_events)
    bbox = R.bbox_of(pts)
    cells, step = R.build_grid(bbox, cell_m)
    R.compute_features(cells, incidents, patrols, now, bbox)
    R.compute_risk(cells)
    return cells, step


def test_risk_is_a_probability():
    cells, _ = _grid_over([_incident(-2.34, 34.82), _incident(-2.341, 34.821)])
    assert cells and all(0.0 <= c.risk <= 1.0 for c in cells)


def test_hotspot_scores_higher_than_edge():
    # five incidents stacked in one corner — the nearest cell must out-rank the far corner
    inc = [_incident(-2.340 + i * 0.0005, 34.820 + i * 0.0005) for i in range(5)]
    cells, _ = _grid_over(inc, cell_m=300.0)
    hot = max(cells, key=lambda c: c.risk)
    cold = min(cells, key=lambda c: c.risk)
    assert hot.risk > cold.risk


def test_lunar_multiplier_in_range():
    # sample a full synodic month — factor stays bounded, never negative
    vals = [R.lunar_risk_multiplier(1704883200.0 + d * 86400) for d in range(30)]
    assert all(0.0 <= v <= 1.0 for v in vals) and max(vals) > min(vals)


def test_patrol_routes_are_unpredictable():
    # THE point of M8: different runs → different routes, or poachers memorize the pattern
    cells, _ = _grid_over([_incident(-2.34, 34.82), _incident(-2.35, 34.83)])
    r1 = R.plan_routes(cells, 3, 6, None, seed=1)
    r2 = R.plan_routes(cells, 3, 6, None, seed=2)
    assert r1 != r2, "different seeds must yield different patrol routes"


def test_seed_reproducible_for_testing():
    cells, _ = _grid_over([_incident(-2.34, 34.82), _incident(-2.35, 34.83)])
    assert R.plan_routes(cells, 3, 6, None, seed=7) == R.plan_routes(cells, 3, 6, None, seed=7)


def test_plan_routes_one_per_ranger():
    cells, _ = _grid_over([_incident(-2.34, 34.82), _incident(-2.35, 34.83)])
    assert len(R.plan_routes(cells, 4, 5, None, seed=1)) == 4


def test_split_events_separates_incidents_and_patrols():
    events = [_incident(-2.34, 34.82),
              {"event_id": "p1", "timestamp": 1782046800, "source_type": "ranger_report",
               "threat_class": "patrol", "confidence": 1.0,
               "coordinates": {"latitude": -2.35, "longitude": 34.83}}]
    incidents, patrols, pts = R.split_events(events)
    assert len(pts) == 2 and len(incidents) >= 1


def test_geojson_export_is_valid_featurecollection():
    cells, step = _grid_over([_incident(-2.34, 34.82)])
    fc = R.cells_to_geojson(cells, step)
    assert fc["type"] == "FeatureCollection" and fc["features"]
    assert "risk_score" in fc["features"][0]["properties"]


def test_stdlib_only():
    src = open(os.path.join(PY, "risk_model.py")).read()
    assert "import numpy" not in src and "import sklearn" not in src
