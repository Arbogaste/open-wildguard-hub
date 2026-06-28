#!/usr/bin/env python3
"""
WildGuard M7 — OSINT scraper for illegal wildlife-trade intelligence.

Traffickers advertise protected species openly on public marketplaces and forums, using coded
slang to dodge keyword filters. This tool fetches public listing pages, scores each against a
maintained slang dictionary, extracts the signals an investigator needs (species, price, location,
seller), and emits structured leads — never an accusation, always flagged for human review.

Design (see dev.md):
    - Offline, stdlib only. No Claude/LLM, no scrapegraphai, no pip install. urllib + re + sqlite3.
    - Rule-based and auditable: every score traces to dictionary terms a human can inspect.
    - Court-aware: each fetched page is SHA-256 hashed at capture (chain of custody, ties to M9).
    - Ethical: PUBLIC pages only. Honors robots.txt, rate-limits, identifies itself in User-Agent.
      Covert access, private groups, or tracked links require legal authorization — out of scope.

What it does NOT do:
    - No login, no private/closed groups, no CAPTCHA bypass, no JS rendering.
    - No auto-blocking or auto-reporting. Output is a lead list for a human analyst / forestry corps.

Input
-----
A text file of public URLs, one per line (`# ` lines and blanks ignored):
    https://some-classifieds.example/search?q=avorio
    https://forum.example/thread/12345

Run
---
    python osint_scrape.py --urls urls.txt
    python osint_scrape.py --urls urls.txt --db osint.db --min-score 3 --events leads.json
    python osint_scrape.py --demo            # offline self-test on a built-in sample page

Output
------
    osint.db        SQLite: every fetched listing + score + extracted fields + evidence hash
    leads.json      Tactical Events (source_type=osint) for listings >= --min-score, to POST to hub
    stdout          ranked briefing of suspected listings for the analyst
"""
import argparse
import hashlib
import html
import json
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
import urllib.robotparser
import uuid
import urllib.parse
from difflib import SequenceMatcher
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

USER_AGENT = "WildGuard-OSINT/1.0 (+conservation wildlife-crime monitoring; contact your-org)"
FETCH_TIMEOUT = 20
RATE_LIMIT_S = 3.0          # politeness delay between requests to the same host
DEFAULT_DICT = os.path.join(os.path.dirname(__file__), "..", "data", "slang_dict.json")

PRICE_RE = re.compile(
    r"(?:€|eur|euro|\$|usd|£|gbp)\s?[\s]?(\d[\d.,]{1,12})|(\d[\d.,]{1,12})\s?(?:€|eur|euro|\$|usd|£|gbp)",
    re.IGNORECASE,
)
# crude location hint: "a Milano", "in Napoli", "zona Roma", "località X"
LOCATION_RE = re.compile(r"\b(?:a|in|zona|localit[aà]|provincia di|near|in)\s+([A-ZÀ-Ý][a-zà-ÿ'\-]{2,30})")
CONTACT_RE = re.compile(r"(?:\+?\d[\d \-]{7,15}\d)|([\w.+-]+@[\w-]+\.[\w.-]+)")


# --------------------------------------------------------------------------- dictionary
def load_dict(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    terms = [(t["term"].lower(), t.get("species", "generic"), int(t.get("weight", 1)))
             for t in d.get("terms", [])]
    hard = [(t["term"].lower(), int(t.get("weight", 1))) for t in d.get("hard_keywords", [])]
    return terms, hard, d.get("version", "?")


# --------------------------------------------------------------------------- fetch
class Fetcher:
    """Polite fetcher: robots.txt cache + per-host rate limiting."""

    def __init__(self):
        self._robots = {}
        self._last_hit = {}

    def _allowed(self, url):
        p = urlparse(url)
        host = f"{p.scheme}://{p.netloc}"
        rp = self._robots.get(host)
        if rp is None:
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(f"{host}/robots.txt")
            try:
                rp.read()
            except Exception:
                rp = None  # no robots.txt reachable → treat as allowed but note it
            self._robots[host] = rp
        if rp is None:
            return True
        return rp.can_fetch(USER_AGENT, url)

    def _throttle(self, url):
        host = urlparse(url).netloc
        last = self._last_hit.get(host, 0)
        wait = RATE_LIMIT_S - (time.time() - last)
        if wait > 0:
            time.sleep(wait)
        self._last_hit[host] = time.time()

    def get(self, url):
        if not self._allowed(url):
            return None, "blocked_by_robots"
        self._throttle(url)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as r:
                raw = r.read(2_000_000)  # cap 2 MB
            return raw, None
        except urllib.error.HTTPError as e:
            return None, f"http_{e.code}"
        except Exception as e:
            return None, f"error_{type(e).__name__}"


# --------------------------------------------------------------------------- parse + score
def strip_html(raw):
    text = raw.decode("utf-8", errors="replace")
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def score_listing(text, terms, hard):
    low = text.lower()
    hits, species_votes, score = [], {}, 0
    for term, species, weight in terms:
        if term in low:
            score += weight
            hits.append(term)
            species_votes[species] = species_votes.get(species, 0) + weight
    for term, weight in hard:
        if term in low:
            score += weight
            hits.append(term)
    species = max(species_votes, key=species_votes.get) if species_votes else None
    return score, hits, species


def extract_fields(text):
    price = None
    m = PRICE_RE.search(text)
    if m:
        price = (m.group(1) or m.group(2) or "").replace(" ", "")
    loc = LOCATION_RE.search(text)
    contact = CONTACT_RE.search(text)
    return {
        "price": price,
        "location": loc.group(1) if loc else None,
        "contact": contact.group(0) if contact else None,
    }


# --------------------------------------------------------------------------- store
def init_db(path):
    con = sqlite3.connect(path)
    con.execute("""CREATE TABLE IF NOT EXISTS listings (
        id TEXT PRIMARY KEY, url TEXT, scraped_at INTEGER, score INTEGER,
        species TEXT, price TEXT, location TEXT, contact TEXT,
        slang_hits TEXT, evidence_sha256 TEXT, excerpt TEXT)""")
    con.execute("CREATE INDEX IF NOT EXISTS idx_listings_score ON listings(score DESC)")
    con.commit()
    return con


TRACKING_PARAMS = ("utm_", "gclid", "fbclid", "_trkparms", "_trksid", "hash", "var", "epid")


def canonicalize_url(url):
    """Strip tracking params + trailing slash + fragment so the same listing dedupes across runs.
    Pattern adapted from Wildlife-News (app/services/dedupe.py)."""
    p = urlparse((url or "").strip())
    q = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=False)
         if not any(k.lower().startswith(t) for t in TRACKING_PARAMS)]
    return urlunparse(p._replace(scheme=(p.scheme or "https").lower(),
                                 netloc=p.netloc.lower(), path=p.path.rstrip("/"),
                                 query=urlencode(sorted(q)), fragment=""))


def dedup_key(url, species, price, location):
    return hashlib.sha256(
        f"{canonicalize_url(url)}|{species}|{price}|{location}".encode("utf-8")).hexdigest()


def collapse_near_dupes(records, title_threshold=0.90):
    """Drop near-duplicate listings (same canonical URL, or >threshold title similarity), keeping
    the highest-scoring one. difflib only — no embeddings, runs on a Pi."""
    kept = []
    for r in sorted(records, key=lambda x: -x.get("score", 0)):
        title = (r.get("excerpt") or "")[:160].lower()
        curl = canonicalize_url(r.get("url", ""))
        dup = False
        for k in kept:
            if canonicalize_url(k.get("url", "")) == curl:
                dup = True
                break
            kt = (k.get("excerpt") or "")[:160].lower()
            if title and kt and SequenceMatcher(None, title, kt).ratio() >= title_threshold:
                dup = True
                break
        if not dup:
            kept.append(r)
    return kept


# --------------------------------------------------------------------------- events
def to_event(rec):
    """Tactical Event (source_type=osint). Matches toolkit/data/event_schema.json (best-effort,
    coordinates unknown for OSINT → null; analyst geolocates from `location` text)."""
    return {
        "event_id": str(uuid.uuid4()),
        "timestamp": rec["scraped_at"],
        "source_type": "osint",
        "source_id": "osint_scrape",
        "coordinates": {"latitude": None, "longitude": None, "elevation": None},
        "threat_class": "wildlife_trade_listing",
        "confidence": min(1.0, rec["score"] / 8.0),
        "evidence_hash": rec["evidence_sha256"],
        "evidence_url": rec["url"],
        "metadata": {
            "title": rec.get("excerpt", "")[:120],
            "score": rec["score"],
            "species_suspected": rec["species"],
            "price": rec["price"],
            "location_text": rec["location"],
            "seller_contact": rec["contact"],
            "slang_terms_found": rec["slang_hits"],
            "source_site": urlparse(rec["url"]).netloc or rec["url"],
            "scraped_at_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(rec["scraped_at"])),
            "needs_human_review": True,
        },
    }


# --------------------------------------------------------------------------- demo page
DEMO_HTML = (
    b"<html><body><h1>Vendo avorio lavorato</h1>"
    b"<p>Bellissimo pezzo, white gold antico, no documenti. Prezzo 1.200 \xe2\x82\xac. "
    b"Disponibile a Napoli. Contatto: +39 333 1234567</p></body></html>"
)


# --------------------------------------------------------------------------- main
def process(url, raw, terms, hard, now):
    text = strip_html(raw)
    score, hits, species = score_listing(text, terms, hard)
    fields = extract_fields(text)
    return {
        "id": dedup_key(url, species, fields["price"], fields["location"]),
        "url": url,
        "scraped_at": now,
        "score": score,
        "species": species,
        "price": fields["price"],
        "location": fields["location"],
        "contact": fields["contact"],
        "slang_hits": hits,
        "evidence_sha256": hashlib.sha256(raw).hexdigest(),
        "excerpt": text[:400],
    }


def main():
    ap = argparse.ArgumentParser(description="WildGuard M7 OSINT wildlife-trade scraper")
    ap.add_argument("--urls", help="text file of public URLs, one per line")
    ap.add_argument("--sites", help="osint_sites.json — expand its search templates with --query")
    ap.add_argument("--query", help="search term used to fill {q} in --sites templates")
    ap.add_argument("--tier", help="only sites with this tier (global/italy/asia/...) when --sites")
    ap.add_argument("--demo", action="store_true", help="run on a built-in sample page, offline")
    ap.add_argument("--dict", default=DEFAULT_DICT, help="slang dictionary JSON")
    ap.add_argument("--db", default="osint.db", help="SQLite output")
    ap.add_argument("--events", help="write Tactical Events JSON for leads >= --min-score")
    ap.add_argument("--min-score", type=int, default=3, help="suspicion threshold for a lead")
    args = ap.parse_args()

    terms, hard, version = load_dict(args.dict)
    print(f"[dict] {len(terms)} slang + {len(hard)} hard keywords (v{version})", file=sys.stderr)

    now = int(time.time())
    records = []

    if args.demo:
        records.append(process("demo://sample-listing", DEMO_HTML, terms, hard, now))
        print("[demo] scored a built-in Italian ivory listing, no network used\n", file=sys.stderr)
    else:
        urls = []
        if args.sites and args.query:
            sites = json.load(open(args.sites, encoding="utf-8")).get("sites", [])
            q = urllib.parse.quote_plus(args.query)
            for s in sites:
                if args.tier and s.get("tier") != args.tier:
                    continue
                if "{q}" in s.get("search", ""):
                    urls.append(s["search"].replace("{q}", q))
            print(f"[sites] {len(urls)} search URLs from {args.sites} for '{args.query}'",
                  file=sys.stderr)
        if args.urls:
            with open(args.urls, encoding="utf-8") as f:
                urls += [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
        if not urls:
            print("Need --urls FILE, or --sites FILE --query TERM, or --demo.", file=sys.stderr)
            return 2
        fetcher = Fetcher()
        for url in urls:
            raw, err = fetcher.get(url)
            if err:
                print(f"[skip] {url} -> {err}", file=sys.stderr)
                continue
            records.append(process(url, raw, terms, hard, now))

    before = len(records)
    records = collapse_near_dupes(records)
    if before != len(records):
        print(f"[dedupe] {before} -> {len(records)} after near-duplicate collapse", file=sys.stderr)

    con = init_db(args.db)
    for r in records:
        con.execute(
            "INSERT OR REPLACE INTO listings VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (r["id"], r["url"], r["scraped_at"], r["score"], r["species"], r["price"],
             r["location"], r["contact"], json.dumps(r["slang_hits"]), r["evidence_sha256"],
             r["excerpt"]))
    con.commit()
    con.close()

    leads = sorted([r for r in records if r["score"] >= args.min_score],
                   key=lambda r: -r["score"])

    if args.events:
        with open(args.events, "w", encoding="utf-8") as f:
            json.dump([to_event(r) for r in leads], f, indent=2, ensure_ascii=False)
        print(f"[ok] {len(leads)} Tactical Events -> {args.events}", file=sys.stderr)

    print("=" * 66)
    print(f"OSINT BRIEFING — {len(records)} listings scanned, "
          f"{len(leads)} flagged (score >= {args.min_score})")
    print("All flags are SUSPECTED and require human review before any action.")
    print("=" * 66)
    for r in leads:
        print(f"\n  score={r['score']}  species={r['species']}  price={r['price']}  "
              f"loc={r['location']}")
        print(f"  url: {r['url']}")
        print(f"  slang: {', '.join(r['slang_hits'])}")
        print(f"  evidence sha256: {r['evidence_sha256'][:16]}...  (chain of custody, M9)")
    if not leads:
        print("\n  No listings over threshold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
