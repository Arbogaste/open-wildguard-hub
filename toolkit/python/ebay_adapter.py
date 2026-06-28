#!/usr/bin/env python3
"""
WildGuard M7 — eBay marketplace adapter for the OSINT scraper.

eBay is a real, public, high-volume marketplace where protected species and parts surface under
coded titles. This adapter turns a search query into individual listing records the M7 scorer can
rank — one row per item, not one row per page.

It ONLY reads public search-results HTML (no login, no API key, no eBay Developer account). It
honours the same politeness rules as osint_scrape.py (User-Agent, rate limit). eBay's Terms of
Service restrict automated access — use this for authorized conservation / law-enforcement
monitoring only, keep request volume low, and prefer eBay's official reporting channel for action.

Each eBay marketplace has its own domain: ebay.it, ebay.com, ebay.de, ebay.co.uk ...

Run
---
    # offline self-test on a saved/sample results page:
    python ebay_adapter.py --demo

    # live (authorized use): search ebay.it for a slang term, score, write leads:
    python ebay_adapter.py --query "avorio antico" --domain ebay.it \
        --events leads.json --min-score 3

    # feed a saved HTML file you downloaded in a browser (most ToS-safe):
    python ebay_adapter.py --html saved_results.html --base https://www.ebay.it

Output: same Tactical Events + SQLite + briefing as osint_scrape.py.
"""
import argparse
import html
import json
import re
import sys
import time
import urllib.parse

import osint_scrape as core  # reuse fetcher, scorer, store, event builder

# eBay search-result item blocks. eBay markup changes; these patterns target the stable
# "s-item" card structure. If eBay restructures, update only these three regexes.
ITEM_BLOCK_RE = re.compile(r'(?is)<li[^>]*class="[^"]*s-item[^"]*".*?</li>')
TITLE_RE = re.compile(r'(?is)<(?:div|span)[^>]*class="[^"]*s-item__title[^"]*"[^>]*>(.*?)</(?:div|span)>')
PRICE_RE = re.compile(r'(?is)<span[^>]*class="[^"]*s-item__price[^"]*"[^>]*>(.*?)</span>')
LINK_RE = re.compile(r'(?is)href="(https?://www\.ebay\.[^"]+/itm/[^"]+)"')


def search_url(domain, query):
    q = urllib.parse.quote_plus(query)
    return f"https://www.{domain}/sch/i.html?_nkw={q}"


def _clean(s):
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def parse_results(page_html, base):
    """Yield (item_url, title, price_text) for each listing card in a results page."""
    for block in ITEM_BLOCK_RE.findall(page_html):
        title = TITLE_RE.search(block)
        price = PRICE_RE.search(block)
        link = LINK_RE.search(block)
        title_txt = _clean(title.group(1)) if title else ""
        if not title_txt or title_txt.lower() in ("shop on ebay", "new listing"):
            continue
        url = link.group(1) if link else base
        yield url, title_txt, (_clean(price.group(1)) if price else None)


DEMO_RESULTS = '''
<ul>
<li class="s-item s-item__pl-on-bottom">
  <a href="https://www.ebay.it/itm/111111">x</a>
  <div class="s-item__title">Antico avorio lavorato - white gold, no documenti</div>
  <span class="s-item__price">1.200,00 EUR</span>
</li>
<li class="s-item">
  <a href="https://www.ebay.it/itm/222222">x</a>
  <div class="s-item__title">Vaso in ceramica decorato vintage</div>
  <span class="s-item__price">35,00 EUR</span>
</li>
<li class="s-item">
  <a href="https://www.ebay.it/itm/333333">x</a>
  <div class="s-item__title">Richiamo vivo da caccia - cardellino selvatico</div>
  <span class="s-item__price">80,00 EUR</span>
</li>
</ul>
'''


def main():
    ap = argparse.ArgumentParser(description="WildGuard M7 eBay adapter")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--query", help="search term (slang or species); fetches eBay live")
    src.add_argument("--html", help="path to a saved eBay results HTML file (ToS-safe)")
    src.add_argument("--demo", action="store_true", help="offline self-test, no network")
    ap.add_argument("--domain", default="ebay.it", help="eBay domain (ebay.it/com/de/co.uk ...)")
    ap.add_argument("--base", default="https://www.ebay.it", help="base URL for --html mode")
    ap.add_argument("--dict", default=core.DEFAULT_DICT)
    ap.add_argument("--db", default="osint.db")
    ap.add_argument("--events")
    ap.add_argument("--min-score", type=int, default=3)
    args = ap.parse_args()

    terms, hard, version = core.load_dict(args.dict)
    print(f"[dict] v{version}  ({len(terms)} slang)", file=sys.stderr)
    now = int(time.time())

    if args.demo:
        page, base = DEMO_RESULTS, "https://www.ebay.it"
        print("[demo] offline eBay results sample\n", file=sys.stderr)
    elif args.html:
        with open(args.html, encoding="utf-8", errors="replace") as f:
            page = f.read()
        base = args.base
    else:
        url = search_url(args.domain, args.query)
        raw, err = core.Fetcher().get(url)
        if err:
            print(f"[fail] {url} -> {err}", file=sys.stderr)
            return 2
        page, base = raw.decode("utf-8", errors="replace"), f"https://www.{args.domain}"

    records = []
    for item_url, title, price_text in parse_results(page, base):
        score, hits, species = core.score_listing(title, terms, hard)
        rec = {
            "id": core.dedup_key(item_url, species, price_text, None),
            "url": item_url, "scraped_at": now, "score": score, "species": species,
            "price": price_text, "location": None,
            "contact": None, "slang_hits": hits,
            "evidence_sha256": core.hashlib.sha256(
                (item_url + title + (price_text or "")).encode("utf-8")).hexdigest(),
            "excerpt": title[:400],
        }
        records.append(rec)

    records = core.collapse_near_dupes(records)
    con = core.init_db(args.db)
    for r in records:
        con.execute("INSERT OR REPLACE INTO listings VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (r["id"], r["url"], r["scraped_at"], r["score"], r["species"], r["price"],
                     r["location"], r["contact"], json.dumps(r["slang_hits"]),
                     r["evidence_sha256"], r["excerpt"]))
    con.commit()
    con.close()

    leads = sorted([r for r in records if r["score"] >= args.min_score], key=lambda r: -r["score"])
    if args.events:
        with open(args.events, "w", encoding="utf-8") as f:
            json.dump([core.to_event(r) for r in leads], f, indent=2, ensure_ascii=False)
        print(f"[ok] {len(leads)} events -> {args.events}", file=sys.stderr)

    print("=" * 60)
    print(f"eBay OSINT — {len(records)} items scanned, {len(leads)} flagged (>= {args.min_score})")
    print("SUSPECTED only. Human review required. Report via eBay + authorities.")
    print("=" * 60)
    for r in leads:
        print(f"\n  score={r['score']}  species={r['species']}  price={r['price']}")
        print(f"  title: {r['excerpt']}")
        print(f"  url:   {r['url']}")
        print(f"  slang: {', '.join(r['slang_hits'])}")
    if not leads:
        print("\n  Nothing over threshold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
