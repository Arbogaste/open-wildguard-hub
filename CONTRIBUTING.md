# Contributing to WildGuard AI

Thank you for helping protect wildlife. This project is built to be **useful in the
field fast**, then improved by the people who actually use it — rangers, researchers,
conservation NGOs, and forestry / wildlife-crime units.

## Ways to contribute (no code required)

- **Slang & keyword terms** (`toolkit/data/slang_dict.json`) — the single highest-impact
  contribution. Add coded trafficking terms for your region/language and priority species,
  each with a `species` and a `weight`. Cite the source (seizure report, academic paper)
  in your PR. Recall of the OSINT tools depends directly on this dictionary.
- **Marketplace / site pointers** (`toolkit/data/osint_sites.json`) — public marketplaces
  and forums where trafficking surfaces, listed **generically** (see legal note below).
- **Field corrections** — flag inaccuracies in the module playbooks (`docs/modules/`).
- **Translations** (`i18n/`, `locales/`) — make the hub usable in more field languages.
- **Open datasets & models** — pointers to freely-licensed camera-trap / bioacoustic
  datasets and pre-trained models that operators can download.

## Code contributions

- Toolkit code is **stdlib-first, offline-first**. Avoid heavy dependencies; a tool must
  run on a Raspberry Pi with no internet where possible. Justify any new dependency.
- Every tool ships a `--demo` mode that runs with zero setup.
- Keep functions auditable: rule-based and inspectable beats a black box for court-facing work.
- Run the tool's `--demo` before submitting. Note what you tested in the PR.

## Legal & ethical rules (non-negotiable)

These are the guardrails that keep the project lawful and the project's users safe.

1. **Public data only.** No login-walled pages, private groups, DMs, or CAPTCHA bypass.
   Covert or authorized undercover investigation is a separate, legally-supervised activity
   and is out of scope for this repo.
2. **Respect robots.txt and site Terms of Service.** Keep request volume low. Prefer
   saved-page / offline parsing modes over live automated scraping.
3. **Never publicly pin a named seller to a suspected crime.** Public output must use
   masked store names and masked listing references — the real URL lives only in the
   secure case file shared with authorities. Doing otherwise is a defamation risk.
4. **No auto-accusation, no auto-reporting.** Tool output is *suspected leads for a human
   analyst*. Reporting to a platform or authority is always a human decision.
5. **Do not commit real scrape data, personal data, or evidence databases** (e.g.
   `osint.db`). These are gitignored. Sample/synthetic data only in the repo.

By contributing you agree your contribution is licensed under the repository's
[MIT License](LICENSE), and that data contributions may be redistributed with the project.

## How to submit

1. Fork, branch, make your change.
2. For dictionary/site data: include the source citation.
3. For code: run `--demo`, describe your test.
4. Open a PR describing *what* changed and *why it helps a field team*.

Not sure where something fits? Open an issue and ask. Field experience is worth more
than polish here.
