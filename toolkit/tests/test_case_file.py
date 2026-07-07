"""
Tests for M9 court evidence (toolkit/python/case_file.py).

This is the module a magistrate relies on: it must prove an evidence file is byte-for-byte the
one captured in the field, and must FAIL loudly (non-zero exit) if a single byte changed. These
tests pin exactly that — the integrity guarantee is the whole point of the chain of custody.
"""
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(HERE, "..", "python")
sys.path.insert(0, PY)

import case_file as CF  # noqa: E402


def _event_with_file(tmp_path, content=b"real evidence frame", wrong_hash=False):
    f = tmp_path / "frame.jpg"
    f.write_bytes(content)
    h = "0" * 64 if wrong_hash else hashlib.sha256(content).hexdigest()
    return {
        "event_id": "evt-court-001", "timestamp": 1782046931,
        "source_type": "camera_trap", "source_id": "CAM_04",
        "coordinates": {"latitude": -2.34, "longitude": 34.84},
        "threat_class": "poacher", "confidence": 0.93,
        "metadata": {"evidence": [{"filename": "frame.jpg", "sha256": h, "captured_by": "CAM_04"}],
                     "custody_log": [{"ts": "2026-06-20T03:42Z", "action": "captured",
                                      "actor": "CAM_04"}]},
    }


def test_matching_hash_passes(tmp_path):
    ev = _event_with_file(tmp_path)
    text, ok = CF.build_case(ev, str(tmp_path))
    assert ok is True and "PASS" in text


def test_tampered_file_fails(tmp_path):
    ev = _event_with_file(tmp_path, wrong_hash=True)
    text, ok = CF.build_case(ev, str(tmp_path))
    assert ok is False and "FAIL" in text and "tampering" in text


def test_missing_file_cannot_verify(tmp_path):
    ev = _event_with_file(tmp_path)
    os.remove(tmp_path / "frame.jpg")
    text, ok = CF.build_case(ev, str(tmp_path))
    assert ok is False and "MISSING FILE" in text


def test_custody_log_appears_in_report(tmp_path):
    ev = _event_with_file(tmp_path)
    text, _ = CF.build_case(ev, str(tmp_path))
    assert "CHAIN OF CUSTODY" in text and "captured" in text and "CAM_04" in text


def test_evidence_items_reads_flat_hash_url():
    # an event carrying only evidence_hash + evidence_url (camera M2 output) still yields an item
    ev = {"evidence_hash": "a" * 64, "evidence_url": "vault/x.jpg", "source_id": "n1"}
    items = CF.evidence_items(ev)
    assert items and items[0]["sha256"] == "a" * 64 and items[0]["filename"] == "x.jpg"


def test_sha256_file_matches_hashlib(tmp_path):
    f = tmp_path / "b.bin"
    f.write_bytes(b"wildguard")
    assert CF.sha256_file(str(f)) == hashlib.sha256(b"wildguard").hexdigest()


def test_cli_demo_exit_zero():
    r = subprocess.run([sys.executable, os.path.join(PY, "case_file.py"), "--demo"],
                       capture_output=True, text=True)
    assert r.returncode == 0 and "ALL PASS" in r.stderr


def test_cli_exit_nonzero_on_tampered_evidence(tmp_path):
    ev = _event_with_file(tmp_path, wrong_hash=True)
    evf = tmp_path / "ev.json"
    evf.write_text(json.dumps(ev))
    r = subprocess.run([sys.executable, os.path.join(PY, "case_file.py"), "--event", str(evf),
                        "--files-dir", str(tmp_path)], capture_output=True, text=True)
    assert r.returncode == 1, "tampered evidence must exit non-zero for scripting/CI"
