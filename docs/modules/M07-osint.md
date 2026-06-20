# M7 — OSINT & Illegal-Market Intelligence (SCAFFOLD)

> Mission: ethical, legal pipeline over forums/social/marketplaces to classify wildlife-trafficking
> ads, decode slang, map smuggling networks, and track price signals to anticipate the next target.

## Recommended repos / tools
| Repo / tool | Take this |
|------|-----------|
| [Wildlife-News](https://github.com/Siddhanthkjain2005/Wildlife-News) | multilingual scrape + dedupe + LLM entity extraction (JSON) + NL query |
| [anti-poaching-platform](https://github.com/lemonadedw/anti-poaching-platform) | parse legal verdicts → smuggling chain + black-market prices |
| [Poaching-Hunting-Uncoop-Env](https://github.com/violentlydave/Poaching-Hunting-in-an-Uncooperative-Environment) | **opsec**: ensure ranger radios/IoT don't leak SSIDs poachers can scan |

Tools: ScrapeGraphAI/Crawl4AI, ExifTool, Docling/Unstructured, AnythingLLM+Ollama (local RAG), GraphRAG.

## Governance
Any infiltration / tracked-link / closed-source collection goes in a separate **authorized
investigative** sublayer with explicit legal authorization + audit. Keep it lawful.

## Milestones
- [ ] Ethical scraper over chosen open sources; dedupe.
- [ ] LLM entity extraction → structured records linked to events.
- [ ] Price-mutation monitor → early-warning per species.

## International use cases
| Context | Adaptation |
|---------|------------|
| Ivory/horn (Africa→Asia routes) | multilingual slang, cross-border graph |
| EU exotic-pet trade | marketplace + social monitoring, GDPR-compliant |
