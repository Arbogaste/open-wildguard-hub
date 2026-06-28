#!/usr/bin/env python3
"""
WildGuard M10 — sensor-node health monitor.

A camera/acoustic node that is dead, flat, or silently offline is a blind spot a poacher can walk
through. This tool reads node heartbeats and raises alerts for low battery, gone-silent nodes, and
weak signal — so a ranger refits the node before the gap is exploited.

Offline, stdlib only.

Input JSON (--file or stdin): array of heartbeats
    [{"node_id":"cam_42","ts":1782046800,"battery_pct":18,"rssi_dbm":-95,"type":"camera_trap"}]

Run
---
    python node_health.py --demo
    python node_health.py --file nodes.json --events node_alerts.json \
        --battery-min 20 --silent-min 120 --rssi-min -90

Output: Tactical Events (source_type=sensor) for each unhealthy node, + status grid.
"""
import argparse
import json
import sys
import time
import uuid


def alert_event(node, threat, conf, note):
    return {
        "event_id": str(uuid.uuid4()),
        "timestamp": int(time.time()),
        "source_type": "sensor",
        "source_id": node.get("node_id", "node"),
        "coordinates": {"latitude": node.get("lat"), "longitude": node.get("lon"),
                        "elevation": None},
        "threat_class": threat,
        "confidence": conf,
        "evidence_hash": None, "evidence_url": None,
        "metadata": {"node_type": node.get("type"), "battery_pct": node.get("battery_pct"),
                     "rssi_dbm": node.get("rssi_dbm"), "note": note, "needs_human_review": True},
    }


DEMO = [
    {"node_id": "cam_01", "ts": None, "battery_pct": 87, "rssi_dbm": -62, "type": "camera_trap"},
    {"node_id": "cam_42", "ts": None, "battery_pct": 14, "rssi_dbm": -71, "type": "camera_trap"},
    {"node_id": "aco_07", "ts": 0,    "battery_pct": 55, "rssi_dbm": -68, "type": "acoustic_node"},
    {"node_id": "cam_19", "ts": None, "battery_pct": 60, "rssi_dbm": -97, "type": "camera_trap"},
]


def main():
    ap = argparse.ArgumentParser(description="WildGuard M10 node health monitor")
    ap.add_argument("--file")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--events")
    ap.add_argument("--battery-min", type=int, default=20, help="alert below this battery %")
    ap.add_argument("--silent-min", type=int, default=120, help="alert if last seen older, minutes")
    ap.add_argument("--rssi-min", type=int, default=-90, help="alert if signal weaker (more negative)")
    args = ap.parse_args()

    now = int(time.time())
    if args.demo:
        nodes = DEMO
        for n in nodes:                       # make 'now' relative for the demo
            if n["ts"] is None:
                n["ts"] = now - 60
            elif n["ts"] == 0:
                n["ts"] = now - 9999           # gone silent
    elif args.file:
        nodes = json.load(open(args.file, encoding="utf-8"))
    elif not sys.stdin.isatty():
        nodes = json.loads(sys.stdin.read())
    else:
        print("Need --file, stdin, or --demo.", file=sys.stderr)
        return 2

    alerts = []
    grid = []
    for n in nodes:
        nid = n.get("node_id", "?")
        bat = n.get("battery_pct")
        rssi = n.get("rssi_dbm")
        silent_min = (now - int(n.get("ts", now))) / 60.0
        flags = []
        if bat is not None and bat < args.battery_min:
            alerts.append(alert_event(n, "node_low_battery", 0.8, f"battery {bat}%"))
            flags.append("LOW-BAT")
        if silent_min > args.silent_min:
            alerts.append(alert_event(n, "node_offline", 0.9, f"silent {int(silent_min)} min"))
            flags.append("OFFLINE")
        if rssi is not None and rssi < args.rssi_min:
            alerts.append(alert_event(n, "node_weak_signal", 0.6, f"rssi {rssi} dBm"))
            flags.append("WEAK-SIG")
        grid.append((nid, bat, rssi, int(silent_min), flags or ["OK"]))

    if args.events:
        json.dump(alerts, open(args.events, "w", encoding="utf-8"), indent=2)
        print(f"[ok] {len(alerts)} events -> {args.events}", file=sys.stderr)

    print("=" * 60)
    print(f"NODE HEALTH — {len(nodes)} nodes, {len(alerts)} alerts")
    print("=" * 60)
    print(f"  {'node':<10} {'bat%':>5} {'rssi':>6} {'silent_m':>9}  status")
    for nid, bat, rssi, sm, flags in grid:
        print(f"  {nid:<10} {str(bat):>5} {str(rssi):>6} {sm:>9}  {' '.join(flags)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
