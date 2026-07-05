"""
Tests for the offline pipeline runner (toolkit/python/wildguard.py).

Everything here runs offline, stdlib only — the same conditions a cloned repo runs in on a
Raspberry Pi. No network, no pip installs beyond pytest itself.

    cd toolkit && python -m pytest tests/ -q
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(HERE, "..", "python")
sys.path.insert(0, PY)

import wildguard  # noqa: E402


def _valid_event(**over):
    ev = {
        "event_id": "e1", "timestamp": 1782046800, "source_type": "camera_trap",
        "coordinates": {"latitude": -2.34, "longitude": 34.82},
        "threat_class": "poacher", "confidence": 0.9,
    }
    ev.update(over)
    return ev


# --------------------------------------------------------------------------- schema validation
def test_valid_event_passes():
    assert wildguard.validate_event(_valid_event(), wildguard.load_schema()) == []


def test_missing_required_field_rejected():
    ev = _valid_event()
    del ev["threat_class"]
    errs = wildguard.validate_event(ev, wildguard.load_schema())
    assert any("threat_class" in e for e in errs)


def test_bad_type_rejected():
    errs = wildguard.validate_event(_valid_event(timestamp="NOT_INT"), wildguard.load_schema())
    assert any("timestamp" in e for e in errs)


def test_bad_enum_rejected():
    errs = wildguard.validate_event(_valid_event(source_type="tiktok"), wildguard.load_schema())
    assert any("source_type" in e for e in errs)


def test_confidence_out_of_range_rejected():
    errs = wildguard.validate_event(_valid_event(confidence=1.7), wildguard.load_schema())
    assert any("confidence" in e and "maximum" in e for e in errs)


def test_nested_coordinates_required_subfield():
    errs = wildguard.validate_event(
        _valid_event(coordinates={"latitude": -2.34}), wildguard.load_schema())
    assert any("longitude" in e for e in errs)


def test_bool_is_not_integer():
    # a JSON true must not satisfy an integer field
    assert wildguard._type_ok(True, "integer") is False
    assert wildguard._type_ok(True, "boolean") is True


# --------------------------------------------------------------------------- ingest
def test_ingest_single_and_array(tmp_path):
    (tmp_path / "one.json").write_text(json.dumps(_valid_event(event_id="a")))
    (tmp_path / "many.json").write_text(json.dumps([_valid_event(event_id="b"),
                                                    _valid_event(event_id="c")]))
    events, errs = wildguard.ingest_dir(str(tmp_path))
    assert len(events) == 3 and errs == []


def test_ingest_reports_bad_json(tmp_path):
    (tmp_path / "broken.json").write_text("{not json")
    events, errs = wildguard.ingest_dir(str(tmp_path))
    assert events == [] and len(errs) == 1


# --------------------------------------------------------------------------- full run via CLI
def _run(args):
    return subprocess.run([sys.executable, os.path.join(PY, "wildguard.py"), *args],
                          capture_output=True, text=True)


def test_demo_full_chain(tmp_path):
    out = tmp_path / "report"
    r = _run(["--demo", "--seed", "1", "--out", str(out)])
    assert r.returncode == 0, r.stderr
    for f in ["events.json", "risk.geojson", "routes.json", "manifest.json", "SUMMARY.txt"]:
        assert (out / f).exists(), f
    m = json.load(open(out / "manifest.json"))
    assert m["events_valid"] == 5 and m["integrity_all_pass"] is True
    assert m["risk"]["top_zones"], "expected ranked risk zones"


def test_malformed_event_goes_to_rejects(tmp_path):
    src = tmp_path / "in"
    src.mkdir()
    (src / "good.json").write_text(json.dumps(_valid_event()))
    (src / "bad.json").write_text(json.dumps(
        {"event_id": "x", "source_type": "tiktok", "confidence": 2}))
    out = tmp_path / "report"
    r = _run(["--events-dir", str(src), "--out", str(out), "--seed", "1"])
    assert r.returncode == 0
    m = json.load(open(out / "manifest.json"))
    assert m["events_valid"] == 1 and m["events_rejected"] == 1
    assert (out / "rejects.json").exists()


def test_tampered_evidence_fails_integrity_exit1(tmp_path):
    src = tmp_path / "in"
    vault = tmp_path / "vault"
    src.mkdir()
    vault.mkdir()
    (vault / "frame.jpg").write_bytes(b"tampered bytes")
    (src / "ev.json").write_text(json.dumps(_valid_event(
        evidence_url="frame.jpg", evidence_hash="deadbeef_wrong_hash")))
    out = tmp_path / "report"
    r = _run(["--events-dir", str(src), "--files-dir", str(vault), "--out", str(out), "--seed", "1"])
    assert r.returncode == 1, "tampered evidence must exit non-zero"
    m = json.load(open(out / "manifest.json"))
    assert m["integrity_all_pass"] is False


def test_real_module_output_flows_through_runner(tmp_path):
    """tip_intake / gps_geofence / node_health --demo → canonical events → runner ingests them.
    Proves the modules and the runner actually speak the same schema."""
    src = tmp_path / "in"
    src.mkdir()
    for mod, fn in [("tip_intake", "tips.json"), ("gps_geofence", "geo.json"),
                    ("node_health", "nodes.json")]:
        rc = subprocess.run([sys.executable, os.path.join(PY, f"{mod}.py"), "--demo",
                             "--events", str(src / fn)], capture_output=True, text=True)
        assert rc.returncode == 0, f"{mod}: {rc.stderr}"
    out = tmp_path / "report"
    r = _run(["--events-dir", str(src), "--out", str(out), "--seed", "1"])
    assert r.returncode == 0, r.stderr
    m = json.load(open(out / "manifest.json"))
    # every real-module event must validate — zero rejects is the integration guarantee
    assert m["events_rejected"] == 0 and m["events_valid"] >= 3
