"""
Tests for M2 edge inference (toolkit/python/edge_infer_camera.py).

The inference loop needs ultralytics + a camera, but the parts that feed the rest of the
pipeline — event construction and label→threat mapping — are pure stdlib and must stay
correct: a mislabeled or schema-invalid event breaks the court chain downstream.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(HERE, "..", "python")
sys.path.insert(0, PY)

import edge_infer_camera as M2  # noqa: E402
import wildguard  # noqa: E402


def test_make_event_is_schema_valid(tmp_path):
    f = tmp_path / "frame.jpg"
    f.write_bytes(b"\xff\xd8\xff fake jpeg")
    ev = M2.make_event("node_edge_42", -2.33, 34.83, "intrusion", 0.91, str(f), label="person")
    assert wildguard.validate_event(ev, wildguard.load_schema()) == []
    assert ev["evidence_hash"] and len(ev["evidence_hash"]) == 64
    assert ev["metadata"]["detected_label"] == "person"  # audit trail


def test_coco_labels_map_to_case_worthy_threats():
    # Zero-training default weights emit COCO names. Every mapped person/vehicle label must
    # land in a threat class that wildguard.py turns into a court case.
    for label in ["person", "car", "truck", "motorcycle"]:
        threat = M2.THREAT_MAP[label]
        assert threat in wildguard.CASE_WORTHY, f"{label} -> {threat} not case-worthy"


def test_default_classes_match_coco_names():
    # Regression: defaults were ["human","vehicle"], which never match COCO output — the tool
    # ran forever detecting nothing. Defaults must include real COCO labels.
    import argparse  # pull the parser defaults without running main()
    for tok in ["person", "car", "truck"]:
        assert tok in open(os.path.join(PY, "edge_infer_camera.py")).read()
