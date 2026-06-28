---
name: wildlife-osint
description: Use when monitoring public online marketplaces (eBay, classifieds, forums) for suspected illegal wildlife-trade listings — building OSINT leads for conservation teams or forestry/law-enforcement corps. Drives the offline, rule-based WildGuard M7 scraper (no LLM, no API key). Triggers — "monitor eBay for ivory", "find wildlife trafficking listings", "OSINT wildlife trade", "scan marketplace for protected species".
---

# Wildlife-Trade OSINT Monitoring

Find and rank suspected illegal wildlife-trade listings on public marketplaces, producing a
review-ready lead list with chain-of-custody evidence hashes. **Rule-based and offline** — it scores
listings against a maintained slang dictionary. No Claude API, no LLM, no marketplace API key.

## Legal & ethical guardrails — read first

- **Public data only.** Search-results pages and public listings. No login, private groups, DMs, or
  CAPTCHA bypass. Covert/authorized investigation is a separate, legally-supervised activity.
- **Respect ToS and robots.txt.** The scraper honours `robots.txt` and rate-limits itself. eBay's ToS
  restricts automation — keep volume low; the **`--html` saved-page mode is the safest** (you download
  the page in a browser, the tool only parses it locally).
- **Never auto-accuse or auto-report.** Output is *suspected* leads for a **human analyst**. Action
  (reporting to the platform + authorities) is a human decision.
- **Generic site list = fine. Naming a specific shop next to a suspected crime = defamation risk.**
  A public dashboard must show a **masked store name + masked listing ref**; the real URL lives only
  in the secure case file (M9) shared with authorities. Listing marketplaces generically (the
  104-site `osint_sites.json`) is legitimate; publicly pinning a named seller to "wildlife crime"
  before adjudication is not.
- **Authorized use:** conservation NGOs, researchers, and forestry/wildlife-crime units.

## Tools (in `toolkit/python/`, `toolkit/data/`)

| File | Role |
|------|------|
| `osint_scrape.py` | Core: fetch public URLs → score → SQLite + Tactical Events + briefing |
| `ebay_adapter.py` | eBay example: search query / saved page → per-item scoring |
| `../data/slang_dict.json` | Editable slang + hard-keyword dictionary (per region/language) |

All stdlib-only. Run `python3 <tool> --demo` first to see output with zero setup.

## Workflow

1. **Tune the dictionary.** Open `toolkit/data/slang_dict.json`. Add region/language slang for your
   priority species (each entry: `term`, `species`, `weight`). This is the single most important step —
   recall depends on it. Review academic papers and seizure reports for current codes.

2. **Pick a source mode** (eBay shown; generalizes to any public site via `osint_scrape.py --urls`):
   - **Saved page (safest, ToS-friendly):** in a browser, search eBay for a slang term, save the
     results page, then:
     ```
     python3 ebay_adapter.py --html saved_results.html --base https://www.ebay.it --events leads.json
     ```
   - **Live (authorized, low volume):**
     ```
     python3 ebay_adapter.py --query "avorio antico" --domain ebay.it --events leads.json --min-score 3
     ```
   - **Other sites / forums:** put public URLs (one per line) in `urls.txt`:
     ```
     python3 osint_scrape.py --urls urls.txt --events leads.json --min-score 3
     ```

3. **Review the briefing.** Each lead shows score, suspected species, price, slang hits, and a
   SHA-256 evidence hash (chain of custody → M9). Verify each by hand before any action.

4. **Wire into the hub (optional).** `leads.json` is an array of Tactical Events (`source_type=osint`).
   POST them to the M0 hub `/events` so OSINT flags appear on the command-center map. A `price_spike`
   signal here can raise an M8 patrol-risk zone — the OSINT → prediction link.

5. **Escalate.** For genuine suspected listings: report through the platform's official channel and to
   the competent authority (e.g. forestry corps / wildlife-crime unit). Keep the evidence hash + URL.

## How scoring works (auditable)

`score = Σ weights of matched slang + hard-keywords` (e.g. "white gold" + "avorio" + "no documenti"
= 9). `--min-score` is the flag threshold. Every score traces to dictionary terms — no black box. To
reduce false positives, lower a term's `weight`; to catch more, add terms or lower `--min-score`.

## Don't

- Don't add an LLM/API to "improve" classification before exhausting the dictionary — keep it offline,
  auditable, and runnable on a Raspberry Pi.
- Don't raise request volume to scrape whole marketplaces — that breaks ToS and politeness. Targeted
  queries on priority species only.
- Don't treat a flag as proof. It is a lead.
