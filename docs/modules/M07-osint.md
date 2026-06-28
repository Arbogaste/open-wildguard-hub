# M7 — OSINT & Illegal-Market Intelligence

> Mission: ethical, legal pipeline over public forums, social media and marketplaces to classify
> wildlife-trafficking ads, decode slang, map smuggling networks, and track price signals.

## 0. Target sites (where to look) — ships as working code

A 104-site target list + rule-based scraper ship in the toolkit. **No LLM, no API key, runs on a Pi.**

- `toolkit/data/osint_sites.json` — 104 public marketplaces/forums with search-URL templates:
  eBay, Subito.it, Amazon, AliExpress, Temu, Alibaba, DHgate, Wish, Etsy, Facebook Marketplace,
  Vinted, Leboncoin, Wallapop, Marktplaats, OLX, Allegro, Avito, MercadoLibre, Taobao/Tmall/JD/
  Xianyu/1688, Shopee, Lazada, Tokopedia, Carousell, Mercari, Yahoo Auctions JP, Rakuten, Flipkart,
  IndiaMART, Daraz, Jiji, Jumia, Trade Me, Catawiki, Delcampe, LiveAuctioneers, 1stDibs, Reddit,
  Telegram(web), Instagram tags … Tiers: global / italy / europe / asia / americas / social_forum / auction.
- `toolkit/data/slang_dict.json` — editable coded-term dictionary (EN + IT seed).
- `toolkit/python/osint_scrape.py` — fetch → score → SQLite + Tactical Events:
  `python osint_scrape.py --sites ../data/osint_sites.json --query avorio --tier italy`
- `toolkit/python/ebay_adapter.py` — worked eBay example (per-item scoring; `--demo` offline).
- `skills/wildlife-osint/SKILL.md` — Claude Code skill driving the above with legal guardrails.

**Public pages only · honour robots.txt + ToS · prefer saved-page (`--html`) mode · human-review every flag.**

## 1. Goal
Poachers and traffickers operate openly on Facebook Marketplace, Telegram groups, classified ad
sites and dark-web forums. Their ads use coded language, slang and emoji to evade detection.
This module builds a monitoring pipeline: scrape public sources, decode species-specific slang,
extract seller locations from EXIF metadata, and build a graph of who sells to whom. Rising prices
for a protected species often predict a poaching spike weeks before it shows up in field data.
Early warning = time to reinforce patrols before the kill happens.

**Legal boundary:** this module only targets public, openly accessible data. Any covert infiltration,
tracked links, or access to private/closed groups requires explicit legal authorization in your
jurisdiction and must be handled in a separate, audited investigative sublayer.

## 2. Field tiers
| Tier | Tooling | What you get |
|------|---------|--------------|
| Essential | Manual Google/Facebook search + spreadsheet logging | ad tracking by hand, free |
| Intermediate | ScrapeGraphAI or Crawl4AI + local Ollama LLM for entity extraction | automated scraping + species/location extraction, no cloud API needed |
| Advanced | Full pipeline: scrape → dedupe → LLM entity extraction → graph DB → price monitor → alerts to hub | structured smuggling network map, price time series, early warning system |

Generalize the OSINT layer beyond news: public registries, marketplace metadata, forum mirrors, and legal/public datasets all fit here if the output can be normalized into species, place, time, actor, and price fields.

## 3. Recommended repos
| Repo / tool | Take this | Notes |
|-------------|-----------|-------|
| [Wildlife-News](https://github.com/Siddhanthkjain2005/Wildlife-News) | multilingual scraper + dedupe + LLM entity extraction → JSON + natural language query | **best starting point**; covers scraping + LLM entity extraction |
| [anti-poaching-platform](https://github.com/lemonadedw/anti-poaching-platform) | parse legal seizure verdicts → structured smuggling chain + black-market price history | use for retrospective analysis of past cases |
| [Poaching-Hunting-Uncoop-Env](https://github.com/violentlydave/Poaching-Hunting-in-an-Uncooperative-Environment) | opsec audit: ensure ranger radios and IoT nodes don't leak SSIDs or GPS coordinates that poachers can scan | run this audit before deploying any sensor network |

Tools: **ScrapeGraphAI** or **Crawl4AI** (ethical scrapers), **ExifTool** (photo GPS extraction), **Ollama + llama3/phi3** (local LLM, no cloud), **AnythingLLM** (local RAG over past cases), **Neo4j** or **NetworkX** (smuggling network graph).

## 4. Slang & species encoding
Wildlife traffickers use coded language that changes frequently. Build and maintain a living slang dictionary per species. Examples (publicly documented in academic literature):
- Ivory: "white gold", "piano keys", "garden furniture"
- Rhino horn: "mineral", "vitamin supplement"
- Pangolin: "artichoke", "pine cone"
- Big cats: "fur coat", "rug"
- Parrots: "love birds"

Your LLM prompt should include current slang terms and ask the model to flag ambiguous listings for human review — never auto-block without a human decision.

## 5. Scripts & workflow
**Scrape + entity extraction pipeline:**
```python
# Uses ScrapeGraphAI + Ollama (local LLM, no cloud)
# pip install scrapegraphai ollama

from scrapegraphai.graphs import SmartScraperGraph

config = {
    "llm": {
        "model": "ollama/phi3",
        "base_url": "http://localhost:11434"
    },
    "verbose": False
}

graph = SmartScraperGraph(
    prompt="""
    Extract all listings that may involve wildlife trade. For each listing return:
    {species_suspected, quantity, price, currency, location_text, seller_id, contact, post_date}
    Flag any of these terms: [paste your slang dictionary here]
    Return JSON array. If no wildlife listings, return empty array.
    """,
    source="https://[target-marketplace-url]/search?q=wildlife",
    config=config
)

results = graph.run()
# results is a list of structured listing dicts
```

**EXIF geolocation from ad photos:**
```bash
# Install ExifTool
# exiftool -GPSLatitude -GPSLongitude -GPSDateStamp photo.jpg
# Automate across a folder:
exiftool -csv -GPSLatitude -GPSLongitude -DateTimeOriginal /path/to/ad/photos/ > photo_gps.csv
# Import into QGIS or the hub map to see where sellers are physically located
```

**Price time series monitor:**
```python
# Store each scraped price in the DB with species + date
# Weekly: run this to detect spikes
import sqlite3, datetime

def price_spike_check(species, threshold_pct=30):
    conn = sqlite3.connect('osint.db')
    rows = conn.execute("""
        SELECT avg(price) as avg_price, strftime('%Y-%W', scraped_at) as week
        FROM listings WHERE species_suspected = ?
        GROUP BY week ORDER BY week DESC LIMIT 8
    """, (species,)).fetchall()
    if len(rows) >= 2:
        latest, prev = rows[0][0], rows[1][0]
        if prev and (latest - prev) / prev * 100 > threshold_pct:
            post_event({'type': 'price_spike_alert', 'payload': {
                'species': species, 'week': rows[0][1],
                'price_change_pct': round((latest-prev)/prev*100, 1)
            }})
```

## 6. Agent prompts
**Prompt A — build the scraping pipeline:**
```
I need an OSINT scraping pipeline for wildlife trafficking intelligence. Build:
1. A Python script using ScrapeGraphAI with a local Ollama model (phi3 or llama3)
2. It scrapes a list of URLs (provided as a text file, one per line)
3. For each page, extracts: {species_suspected, quantity, price, currency, location_text,
   seller_contact, post_date, source_url, slang_terms_found}
4. Deduplicates listings by (species, price, location, date) similarity
5. Stores results in SQLite and posts each unique finding as a Tactical Event to the hub
Include the slang dictionary as a configurable JSON file, not hardcoded.
```

**Prompt B — smuggling network graph:**
```
I have a SQLite table 'listings' with columns (seller_id, buyer_contact, species, location, date).
Build a Python script using NetworkX that:
1. Creates a directed graph: seller -> buyer per transaction
2. Identifies the top 10 highest-degree nodes (most connected traffickers)
3. Detects communities (clusters of interconnected sellers/buyers)
4. Exports the graph as a GeoJSON (nodes = sellers, edges = transactions, coords from EXIF data)
5. Outputs a summary: top nodes, community count, largest community size
```

**Prompt C — early warning report:**
```
Every Monday, generate an early warning report from the OSINT database. The report should:
1. List species with price increase >20% vs. 4-week average
2. List new sellers who appeared in the last 7 days with >3 listings
3. List locations with spike in listing density (new hotspot)
4. Cross-reference with M8 patrol risk zones: flag if a spike area overlaps a high-risk zone
Output as a plain-text briefing and a JSON summary for the hub.
```

## 7. Milestones (clone-and-follow checklist)
- [ ] Clone Wildlife-News repo. Run the scraper on one public test source. Confirm entity extraction works.
- [ ] Build and maintain a species slang dictionary for your region. Review academic papers and law enforcement reports for current terms.
- [ ] Set up local Ollama with phi3 or llama3. Confirm it runs offline on your hardware.
- [ ] Run ExifTool on a sample set of known trafficking photos (from public law enforcement case files). Map GPS coordinates.
- [ ] Ingest 30 days of public marketplace listings. Spot-check extraction accuracy. Target >80% species match recall.
- [ ] Build price time series for your top-3 priority species. Baseline established.
- [ ] Wire price spike + new seller alerts to hub /events. Confirm they appear on the dashboard.
- [ ] Weekly: run Prompt C early warning report. Brief intelligence analyst. Adjust patrol plan (M8).

## 8. International use cases
| Context | Adaptation |
|---------|------------|
| Ivory / horn (Africa → Asia routes) | multilingual slang dictionary (Chinese, Vietnamese, Thai); cross-border seller network graph |
| EU exotic pet trade | Facebook Marketplace + classified sites; GDPR-compliant scraping (public posts only); link to CITES permit database |
| Timber / charcoal trafficking | species-specific wood slang; truck plate extraction from EXIF; route mapping |
| Marine species (shark fin, abalone) | restaurant supply network monitoring; price signal from wholesale markets |
| Online auction platforms | image classifier (M2 model) to auto-flag photos containing protected species parts |
