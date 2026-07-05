#!/usr/bin/env python3
"""
WildGuard — offline pipeline runner (the hub's job, without a server).

Every detector in this toolkit writes the same thing: a canonical Tactical Event JSON
(camera M2, acoustic M3, collar/geofence M5, tips M6, OSINT M7...). On their own they are
islands — a ranger has to run each script by hand and copy JSON between them. This runner is
the connective tissue: point it at the folder your detectors write to and it does, in order,
offline, stdlib only:

    1. INGEST    read every events/*.json (single event or array), flatten
    2. VALIDATE  enforce ../data/event_schema.json at ingestion (rejects go to a rejects file,
                 never silently into the case) — the schema gap goal.md flagged
    3. ENRICH    (optional, --enrich, needs network) taxonomy + coordinates via M5 species_lookup
    4. RISK      M8 risk grid + unpredictable patrol routes over the real incident locations
    5. CASE      M9 court-ready case file + SHA-256 integrity for each threat event above a
                 confidence threshold
    6. BUNDLE    write one operator folder: validated events, risk.geojson, routes.json,
                 cases/*.txt, manifest.json, SUMMARY.txt

No hub, no backend, no cloud. Runs on a Raspberry Pi from a USB stick. This is what turns ten
separate scripts into one deployable workflow a field team can actually adopt.

Run
---
    python wildguard.py --demo                       # synthesizes events, runs the whole chain
    python wildguard.py --events-dir events/ --out report/
    python wildguard.py --events-dir events/ --out report/ --enrich   # + live M5 (network)

Exit code is non-zero if any evidence file FAILS its integrity check (tampering signal).
"""
import argparse
import json
import os
import sys
import time
import uuid

# Sibling toolkit modules (same dir). All stdlib, safe to import as libraries.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import risk_model
import case_file
try:
    import species_lookup  # only needed for --enrich (network)
except Exception:  # pragma: no cover
    species_lookup = None

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "event_schema.json")

# Threat classes that deserve a court-ready case file (M9). Others (e.g. animal sightings) don't.
CASE_WORTHY = {"poacher", "vehicle", "weapon", "gunshot", "chainsaw", "snare", "intrusion",
               "geofence_breach"}


# --------------------------------------------------------------------------- schema validation
def load_schema():
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


def _type_ok(val, jtype):
    """Draft-07 type check for the subset our schema uses (with number/integer distinction)."""
    if isinstance(jtype, list):
        return any(_type_ok(val, t) for t in jtype)
    if jtype == "null":
        return val is None
    if jtype == "string":
        return isinstance(val, str)
    if jtype == "integer":
        return isinstance(val, int) and not isinstance(val, bool)
    if jtype == "number":
        return isinstance(val, (int, float)) and not isinstance(val, bool)
    if jtype == "object":
        return isinstance(val, dict)
    if jtype == "array":
        return isinstance(val, list)
    if jtype == "boolean":
        return isinstance(val, bool)
    return True


def validate_event(ev, schema):
    """Return a list of human-readable errors (empty list = valid). Minimal draft-07 subset:
    required, type, enum, minimum/maximum, and one level of nested required/type (coordinates).
    Enough to keep malformed detector output out of a court case."""
    errors = []
    if not isinstance(ev, dict):
        return ["event is not a JSON object"]
    props = schema.get("properties", {})
    for key in schema.get("required", []):
        if key not in ev:
            errors.append(f"missing required field '{key}'")
    for key, val in ev.items():
        spec = props.get(key)
        if not spec:
            continue
        if "type" in spec and not _type_ok(val, spec["type"]):
            errors.append(f"field '{key}' has wrong type (want {spec['type']})")
            continue
        if "enum" in spec and val not in spec["enum"]:
            errors.append(f"field '{key}'={val!r} not in {spec['enum']}")
        if "minimum" in spec and isinstance(val, (int, float)) and val < spec["minimum"]:
            errors.append(f"field '{key}'={val} < minimum {spec['minimum']}")
        if "maximum" in spec and isinstance(val, (int, float)) and val > spec["maximum"]:
            errors.append(f"field '{key}'={val} > maximum {spec['maximum']}")
        # one level deep for the nested coordinates object
        if spec.get("type") == "object" and isinstance(val, dict):
            for sub in spec.get("required", []):
                if sub not in val:
                    errors.append(f"field '{key}' missing required sub-field '{sub}'")
    return errors


# --------------------------------------------------------------------------- ingest
def ingest_dir(path):
    """Read every *.json under path. Each file is a single event or an array. Returns
    (events, read_errors)."""
    events, read_errors = [], []
    for name in sorted(os.listdir(path)):
        if not name.endswith(".json"):
            continue
        fp = os.path.join(path, name)
        try:
            data = json.load(open(fp, encoding="utf-8"))
        except Exception as e:
            read_errors.append(f"{name}: unreadable JSON ({e})")
            continue
        for ev in (data if isinstance(data, list) else [data]):
            ev.setdefault("_source_file", name)
            events.append(ev)
    return events, read_errors


def synth_events():
    """A handful of realistic Tactical Events so --demo runs the full chain with zero setup."""
    now = int(time.time())
    base_lat, base_lon = -2.34, 34.82
    out = []
    hotspots = [(0.02, 0.03, "poacher", 0.93, "camera_trap", "CAM_TRAP_04"),
                (0.018, 0.028, "gunshot", 0.88, "acoustic_node", "ACO_07"),
                (0.021, 0.031, "vehicle", 0.71, "camera_trap", "CAM_TRAP_11"),
                (-0.03, -0.02, "geofence_breach", 0.99, "gps_collar", "ELE_07"),
                (0.005, -0.01, "chainsaw", 0.66, "acoustic_node", "ACO_03")]
    for i, (dlat, dlon, threat, conf, stype, sid) in enumerate(hotspots):
        out.append({
            "event_id": str(uuid.uuid4()),
            "timestamp": now - i * 3600,
            "source_type": stype, "source_id": sid,
            "coordinates": {"latitude": base_lat + dlat, "longitude": base_lon + dlon,
                            "elevation": None},
            "threat_class": threat, "confidence": conf,
            "evidence_hash": None, "evidence_url": None,
            "metadata": {"species_suspected": "African elephant" if threat == "geofence_breach"
                         else None},
        })
    return out


# --------------------------------------------------------------------------- pipeline stages
def stage_risk(events, out_dir, args):
    """M8: risk grid + patrol routes over the validated incident locations."""
    incidents, patrols, pts = risk_model.split_events(events)
    if not pts:
        return None
    now = int(time.time())
    bbox = risk_model.bbox_of(pts)
    cells, step = risk_model.build_grid(bbox, args.cell_m)
    risk_model.compute_features(cells, incidents, patrols, now, bbox)
    risk_model.compute_risk(cells)
    routes = risk_model.plan_routes(cells, args.rangers, args.waypoints, None, seed=args.seed)

    geo_path = os.path.join(out_dir, "risk.geojson")
    route_path = os.path.join(out_dir, "routes.json")
    with open(geo_path, "w") as f:
        json.dump(risk_model.cells_to_geojson(cells, step), f, indent=2)
    with open(route_path, "w") as f:
        json.dump(risk_model.routes_to_json(routes), f, indent=2)

    top = sorted(cells, key=lambda c: getattr(c, "risk", 0.0), reverse=True)[:3]
    top_zones = [{"cell": c.cid, "lat": round(c.lat, 5), "lon": round(c.lon, 5),
                  "risk": round(getattr(c, "risk", 0.0), 3)} for c in top]
    return {"cells": len(cells), "rangers": len(routes), "top_zones": top_zones,
            "geojson": os.path.basename(geo_path), "routes": os.path.basename(route_path)}


def stage_cases(events, out_dir, files_dir, min_conf):
    """M9: a court-ready case file + integrity check for each threat event above threshold."""
    cases_dir = os.path.join(out_dir, "cases")
    os.makedirs(cases_dir, exist_ok=True)
    made, all_pass = [], True
    for ev in events:
        if ev.get("threat_class") not in CASE_WORTHY:
            continue
        if (ev.get("confidence") or 0) < min_conf:
            continue
        text, ok = case_file.build_case(ev, files_dir)
        all_pass = all_pass and ok
        cid = (ev.get("event_id") or "unknown")[:18]
        fp = os.path.join(cases_dir, f"{cid}.txt")
        open(fp, "w", encoding="utf-8").write(text)
        made.append({"event_id": ev.get("event_id"), "threat": ev.get("threat_class"),
                     "file": os.path.join("cases", f"{cid}.txt"), "integrity_pass": ok})
    return made, all_pass


# --------------------------------------------------------------------------- run
def run(args):
    os.makedirs(args.out, exist_ok=True)
    schema = load_schema()
    log = lambda m: print(m, file=sys.stderr)

    # 1. INGEST
    read_errors = []
    if args.demo:
        events = synth_events()
        log(f"[demo] synthesized {len(events)} events (no events-dir needed)")
    else:
        if not args.events_dir or not os.path.isdir(args.events_dir):
            log("Need --events-dir DIR (folder your detectors write to), or --demo.")
            return 2
        events, read_errors = ingest_dir(args.events_dir)
        log(f"[ingest] {len(events)} events from {args.events_dir}")

    # 2. VALIDATE — enforce the schema at ingestion
    valid, rejects = [], []
    for ev in events:
        errs = validate_event(ev, schema)
        if errs:
            rejects.append({"source_file": ev.get("_source_file"), "errors": errs, "event": ev})
        else:
            valid.append(ev)
    for ev in valid:
        ev.pop("_source_file", None)
    if rejects:
        with open(os.path.join(args.out, "rejects.json"), "w", encoding="utf-8") as f:
            json.dump(rejects, f, indent=2, ensure_ascii=False)
    log(f"[validate] {len(valid)} valid, {len(rejects)} rejected"
        + (" -> rejects.json" if rejects else ""))
    if not valid:
        log("No valid events. Nothing to process.")
        return 2

    # 3. ENRICH (optional, network)
    if args.enrich:
        if species_lookup is None:
            log("[enrich] species_lookup unavailable — skipping")
        else:
            token = os.environ.get("IUCN_TOKEN")
            log("[enrich] M5 taxonomy + geocode (network, ~1 req/s)...")
            species_lookup.enrich_events(valid, token)

    # persist validated events (the merged store the killed hub would have held)
    with open(os.path.join(args.out, "events.json"), "w", encoding="utf-8") as f:
        json.dump(valid, f, indent=2, ensure_ascii=False)

    # 4. RISK
    risk_summary = stage_risk(valid, args.out, args)
    if risk_summary:
        log(f"[risk] {risk_summary['cells']} cells, {risk_summary['rangers']} patrol routes")
    else:
        log("[risk] no usable coordinates — skipped")

    # 5. CASES
    cases, all_pass = stage_cases(valid, args.out, args.files_dir, args.min_conf)
    log(f"[cases] {len(cases)} case file(s)"
        + ("" if all_pass else "  ** INTEGRITY FAILURE PRESENT **"))

    # 6. BUNDLE — manifest + human summary
    manifest = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "events_total": len(events), "events_valid": len(valid),
        "events_rejected": len(rejects), "read_errors": read_errors,
        "enriched": bool(args.enrich), "risk": risk_summary, "cases": cases,
        "integrity_all_pass": all_pass,
    }
    with open(os.path.join(args.out, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    write_summary(args.out, manifest)

    log(f"\n[ok] bundle -> {args.out}/  (events.json, risk.geojson, routes.json, "
        f"cases/, manifest.json, SUMMARY.txt)")
    return 0 if all_pass else 1


def write_summary(out_dir, m):
    L = []
    L.append("=" * 60)
    L.append("WILDGUARD FIELD BRIEFING")
    L.append(f"generated {m['generated_at']}")
    L.append("=" * 60)
    L.append(f"events ingested : {m['events_total']}")
    L.append(f"events valid    : {m['events_valid']}")
    L.append(f"events rejected : {m['events_rejected']}"
             + ("  (see rejects.json)" if m['events_rejected'] else ""))
    L.append("")
    if m["risk"] and m["risk"]["top_zones"]:
        L.append("TOP RISK ZONES (patrol these first):")
        for i, z in enumerate(m["risk"]["top_zones"], 1):
            L.append(f"  {i}. cell {z['cell']}  @ {z['lat']},{z['lon']}  risk={z['risk']}")
        L.append(f"  -> {m['risk']['rangers']} unpredictable patrol routes in routes.json")
        L.append("")
    if m["cases"]:
        L.append("COURT-READY CASES (M9):")
        for c in m["cases"]:
            flag = "PASS" if c["integrity_pass"] else "FAIL ** possible tampering **"
            L.append(f"  - {c['threat']:<16} {c['file']}   integrity={flag}")
        L.append("")
    L.append(f"EVIDENCE INTEGRITY: {'ALL PASS' if m['integrity_all_pass'] else 'FAILURES PRESENT'}")
    L.append("=" * 60)
    open(os.path.join(out_dir, "SUMMARY.txt"), "w", encoding="utf-8").write("\n".join(L))


def main():
    ap = argparse.ArgumentParser(
        description="WildGuard offline pipeline runner (ingest -> validate -> risk -> case files)")
    ap.add_argument("--events-dir", help="folder your detectors write Tactical Event JSON into")
    ap.add_argument("--out", default="report", help="output bundle folder (default: report/)")
    ap.add_argument("--files-dir", help="folder holding evidence files, for M9 integrity checks")
    ap.add_argument("--enrich", action="store_true", help="run M5 taxonomy/geocode (needs network)")
    ap.add_argument("--min-conf", type=float, default=0.5, help="min confidence for a case file")
    ap.add_argument("--cell-m", type=float, default=500.0, help="risk grid cell size (meters)")
    ap.add_argument("--rangers", type=int, default=4)
    ap.add_argument("--waypoints", type=int, default=8)
    ap.add_argument("--seed", type=int, help="fix randomness (testing only — NOT in the field)")
    ap.add_argument("--demo", action="store_true", help="synthesize events and run the full chain")
    args = ap.parse_args()
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
