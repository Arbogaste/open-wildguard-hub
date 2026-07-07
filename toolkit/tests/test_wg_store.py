"""
Tests for the single-file SQLite store (toolkit/python/wg_store.py).

Guarantees a researcher/ranger depends on: ingest is idempotent (no duplicate incidents),
spatial + temporal + confidence filters actually filter, and the exports are the real formats
QGIS / GBIF expect. All stdlib, offline.
"""
import csv
import json
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(HERE, "..", "python")
sys.path.insert(0, PY)

import wg_store as S  # noqa: E402


def _ev(eid, lat, lon, threat, conf, ts, **meta):
    e = {"event_id": eid, "timestamp": ts, "source_type": "camera_trap", "source_id": "n1",
         "coordinates": {"latitude": lat, "longitude": lon}, "threat_class": threat,
         "confidence": conf}
    if meta:
        e["metadata"] = meta
    return e


def _seed(tmp_path):
    p = tmp_path / "events.json"
    p.write_text(json.dumps([
        _ev("a", -2.34, 34.82, "gunshot", 0.9, 1780000000),
        _ev("b", -2.35, 34.83, "poacher", 0.6, 1781000000),
        _ev("c", -8.00, 40.00, "gunshot", 0.95, 1782000000),  # far away
    ]))
    db = str(tmp_path / "r.sqlite")
    S.ingest(db, str(p))
    return db


def test_ingest_idempotent(tmp_path):
    db = _seed(tmp_path)
    S.ingest(db, str(tmp_path / "events.json"))  # second time
    n = sqlite3.connect(db).execute("SELECT COUNT(*) FROM events").fetchone()[0]
    assert n == 3, "re-ingest must update in place, not duplicate"


def test_ingest_folder(tmp_path):
    d = tmp_path / "events"
    d.mkdir()
    (d / "one.json").write_text(json.dumps(_ev("x", -2.3, 34.8, "snare", 0.8, 1780000000)))
    (d / "two.json").write_text(json.dumps([_ev("y", -2.3, 34.8, "vehicle", 0.7, 1780000001)]))
    db = str(tmp_path / "r.sqlite")
    assert S.ingest(db, str(d)) == 2


def test_query_by_type(tmp_path):
    db = _seed(tmp_path)
    assert {e["event_id"] for e in S.query(db, threat_class="gunshot")} == {"a", "c"}


def test_query_min_conf(tmp_path):
    db = _seed(tmp_path)
    assert {e["event_id"] for e in S.query(db, min_conf=0.9)} == {"a", "c"}


def test_query_since_accepts_iso(tmp_path):
    db = _seed(tmp_path)
    got = {e["event_id"] for e in S.query(db, since="2026-06-01")}  # ~1780+ range
    # only events at/after 2026-06-01 UTC
    assert "c" in got and "a" not in got


def test_query_near_radius(tmp_path):
    db = _seed(tmp_path)
    near = S.query(db, near=(-2.34, 34.82), radius_km=20)
    ids = {e["event_id"] for e in near}
    assert "a" in ids and "b" in ids and "c" not in ids  # c is ~1000 km away


def test_haversine_sanity():
    # ~1 degree of latitude ≈ 111 km
    assert 110 < S.haversine_km(0, 0, 1, 0) < 112


def test_export_csv_is_readable(tmp_path):
    db = _seed(tmp_path)
    out = str(tmp_path / "e.csv")
    S.export_csv(S.query(db), out)
    rows = list(csv.DictReader(open(out)))
    assert len(rows) == 3 and rows[0]["latitude"] and "threat_class" in rows[0]


def test_export_geojson_structure(tmp_path):
    db = _seed(tmp_path)
    out = str(tmp_path / "e.geojson")
    S.export_geojson(S.query(db), out)
    d = json.load(open(out))
    assert d["type"] == "FeatureCollection" and len(d["features"]) == 3
    # GeoJSON is lon,lat order — a classic bug source
    f = d["features"][0]
    assert f["geometry"]["coordinates"][0] > 34 and f["geometry"]["coordinates"][1] < 0


def test_export_darwincore_terms(tmp_path):
    db = _seed(tmp_path)
    out = str(tmp_path / "occ.csv")
    S.export_darwincore(S.query(db), out)
    rows = list(csv.DictReader(open(out)))
    assert "decimalLatitude" in rows[0] and "occurrenceID" in rows[0]
    assert rows[0]["basisOfRecord"] == "MachineObservation"


def test_darwincore_uses_enriched_species(tmp_path):
    p = tmp_path / "ev.json"
    p.write_text(json.dumps(_ev("z", -2.3, 34.8, "poacher", 0.9, 1782000000,
                                taxonomy={"scientific_name": "Loxodonta africana"})))
    db = str(tmp_path / "r.sqlite")
    S.ingest(db, str(p))
    out = str(tmp_path / "occ.csv")
    S.export_darwincore(S.query(db), out)
    row = list(csv.DictReader(open(out)))[0]
    assert row["scientificName"] == "Loxodonta africana"
