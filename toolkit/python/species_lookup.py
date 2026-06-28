#!/usr/bin/env python3
"""
WildGuard M5 — species & place enrichment via free public APIs.

A detection or an OSINT listing usually arrives with a messy name ("avorio", "cardellino",
"elephant ivory") and a place written as text ("Napoli"). This tool turns those into clean,
shareable facts:
    - the accepted scientific name + taxonomy           → GBIF  (no key)
    - the IUCN Red List conservation status             → IUCN  (free token, optional)
    - coordinates from a place name, or a place name
      from coordinates                                  → Nominatim / OpenStreetMap (no key)

Why it matters: a report that says "Acridotheres / Least Concern, near 40.85,14.27" is far more
useful to a ranger or a magistrate than "uccello a Napoli". It also lets OSINT events (which have
no GPS) land on the hub map.

Stdlib only (urllib). Each call is one public HTTPS GET. Be polite: low volume, identify yourself.

APIs used (and the project that inspired each)
    GBIF species match   https://api.gbif.org/v1/species/match?name=NAME           (audtheia-environmental-monitoring)
    IUCN Red List v3     https://apiv3.iucnredlist.org/api/v3/species/NAME?token=…  (audtheia; needs a free token)
    Nominatim geocode    https://nominatim.openstreetmap.org/search|reverse         (audtheia)

Run
---
    python species_lookup.py --demo                         # offline, no network
    python species_lookup.py --name "African elephant"      # live GBIF
    python species_lookup.py --place "Napoli, Italy"        # live geocode
    python species_lookup.py --lat -2.34 --lon 34.82        # live reverse geocode
    python species_lookup.py --enrich events.json --out enriched.json   # batch-enrich Tactical Events
    IUCN_TOKEN=xxxx python species_lookup.py --name "Panthera tigris"   # add Red List status
"""
import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request

UA = "WildGuard-M5/1.0 (+open-source conservation; contact your-org)"


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


# --------------------------------------------------------------------------- GBIF (no key)
def gbif_match(name):
    """Accepted scientific name + taxonomy for a (possibly fuzzy) name. https://www.gbif.org/developer/species"""
    url = "https://api.gbif.org/v1/species/match?" + urllib.parse.urlencode({"name": name})
    d = _get(url)
    return {
        "input": name,
        "matched": d.get("matchType") != "NONE",
        "scientific_name": d.get("scientificName"),
        "rank": d.get("rank"),
        "kingdom": d.get("kingdom"), "class": d.get("class"),
        "order": d.get("order"), "family": d.get("family"),
        "gbif_usage_key": d.get("usageKey"),
        "confidence": d.get("confidence"),
    }


# --------------------------------------------------------------------------- IUCN (free token)
def iucn_status(name, token):
    """Red List category (EX/CR/EN/VU/NT/LC/…). Get a free token at https://apiv3.iucnredlist.org/api/v3/token"""
    if not token:
        return {"status": None, "note": "set IUCN_TOKEN for Red List status"}
    url = (f"https://apiv3.iucnredlist.org/api/v3/species/"
           f"{urllib.parse.quote(name)}?token={urllib.parse.quote(token)}")
    d = _get(url)
    res = (d.get("result") or [{}])[0]
    return {"status": res.get("category"), "population_trend": res.get("population_trend"),
            "iucn_taxonid": res.get("taxonid")}


# --------------------------------------------------------------------------- Nominatim (no key)
def geocode(place):
    """Place text → coordinates. OSM Nominatim. Usage policy: max 1 req/s, identify yourself."""
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": place, "format": "json", "limit": 1})
    d = _get(url)
    if not d:
        return {"lat": None, "lon": None, "display_name": None}
    return {"lat": float(d[0]["lat"]), "lon": float(d[0]["lon"]),
            "display_name": d[0].get("display_name")}


def reverse_geocode(lat, lon):
    url = "https://nominatim.openstreetmap.org/reverse?" + urllib.parse.urlencode(
        {"lat": lat, "lon": lon, "format": "json"})
    d = _get(url)
    return {"display_name": d.get("display_name"), "address": d.get("address", {})}


# --------------------------------------------------------------------------- batch enrich
def enrich_events(events, token):
    """Fill taxonomy + conservation status + coordinates on Tactical Events in place.
    Polite: ~1 req/s. Reads metadata.species_suspected and metadata.location_text."""
    for ev in events:
        m = ev.setdefault("metadata", {})
        name = m.get("species_suspected") or ev.get("threat_class")
        if name and name not in ("generic", None):
            try:
                m["taxonomy"] = gbif_match(name)
                m["conservation"] = iucn_status(m["taxonomy"].get("scientific_name") or name, token)
            except Exception as e:
                m["taxonomy_error"] = str(e)
            time.sleep(1.0)
        c = ev.get("coordinates", {})
        if (c.get("latitude") is None) and m.get("location_text"):
            try:
                g = geocode(m["location_text"])
                if g["lat"] is not None:
                    ev["coordinates"] = {"latitude": g["lat"], "longitude": g["lon"],
                                         "elevation": None}
                    m["geocoded_from"] = m["location_text"]
            except Exception as e:
                m["geocode_error"] = str(e)
            time.sleep(1.0)
    return events


DEMO = {
    "taxonomy": {"input": "African elephant", "matched": True,
                 "scientific_name": "Loxodonta africana", "rank": "SPECIES",
                 "kingdom": "Animalia", "class": "Mammalia", "order": "Proboscidea",
                 "family": "Elephantidae", "gbif_usage_key": 2433722, "confidence": 98},
    "conservation": {"status": "EN", "population_trend": "decreasing", "note": "demo value"},
    "geocode": {"lat": 40.8358, "lon": 14.2488, "display_name": "Napoli, Campania, Italia"},
}


def main():
    ap = argparse.ArgumentParser(description="WildGuard M5 species & place enrichment")
    ap.add_argument("--name", help="species name → GBIF taxonomy (+ IUCN if token)")
    ap.add_argument("--place", help="place text → coordinates")
    ap.add_argument("--lat", type=float)
    ap.add_argument("--lon", type=float)
    ap.add_argument("--enrich", help="Tactical Events JSON to enrich")
    ap.add_argument("--out", help="write enriched events here")
    ap.add_argument("--demo", action="store_true", help="offline sample, no network")
    args = ap.parse_args()
    token = os.environ.get("IUCN_TOKEN")

    if args.demo:
        print(json.dumps(DEMO, indent=2, ensure_ascii=False))
        print("\n[demo] sample only — drop --demo and use --name/--place for live API calls",
              file=sys.stderr)
        return 0
    if args.enrich:
        events = json.load(open(args.enrich, encoding="utf-8"))
        events = enrich_events(events if isinstance(events, list) else [events], token)
        out = args.out or args.enrich.replace(".json", "_enriched.json")
        json.dump(events, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        print(f"[ok] enriched -> {out}", file=sys.stderr)
        return 0
    result = {}
    if args.name:
        result["taxonomy"] = gbif_match(args.name)
        result["conservation"] = iucn_status(
            result["taxonomy"].get("scientific_name") or args.name, token)
    if args.place:
        result["geocode"] = geocode(args.place)
    if args.lat is not None and args.lon is not None:
        result["reverse_geocode"] = reverse_geocode(args.lat, args.lon)
    if not result:
        print("Give --name / --place / --lat+--lon / --enrich, or --demo.", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
