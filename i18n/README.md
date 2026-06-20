# i18n — interface translations

The dashboard (`index.html`) is translatable into ~20 languages via a language selector.

- `en.json` and `it.json` are the **source of truth** and are also bundled inline in `index.html`
  (so the page renders offline on first paint).
- All other languages load on demand from `i18n/<code>.json`. **Any missing key falls back to English**,
  so a partial translation is fine — it never breaks the UI.

## Add / translate a language
1. Copy `en.json` to `i18n/<code>.json` (e.g. `es.json`, `sw.json`).
2. Translate the **values** only. Keep the **keys** identical.
3. The language already appears in the selector if its code is in the `LANGS` array in `index.html`.
   To add a new code, add `['<code>', '<Native name>']` to that array.

## Target languages (in the selector)
en, it, es, fr, de, pt, ru, zh, hi, ar, sw, id, fa, tr, vi, th, bn, ja, ko, uk

Translated so far: **en, it**. The rest fall back to English until their `i18n/<code>.json` exists.

> Tip: hand `en.json` to a translation agent and ask for one JSON file per language code above.

Note: the older `../locales/*.json` files use a different, unused key namespace and are **not wired**
to the dashboard. This `i18n/` directory is the active system.
