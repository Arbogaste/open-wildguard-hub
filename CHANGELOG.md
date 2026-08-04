# WildGuard AI — changelog sessioni

> Storico tecnico. Obiettivo e prossimi passi → `goal.md`. Piano milestone → `PLAN.md`.

### open-wildguard-hub — sessione 2026-08-03 (privacy notice del sito pubblico)
- **`privacy.html`** (EN, standalone, palette del hub): titolare = maintainer del progetto, log hosting Vercel,
  `localStorage` (`wildguard_lang`), tiles CARTO come terza parte, nessun cookie/analytics/ads, diritti + Garante.
  Linkata da `index.html` (footer credits), `readme.html` (header), `scriptplay.html` (header).
- **Verifica sul codice, non sulle intenzioni**: il commento in `index.html` dice "Leaflet self-hosted", ma
  `L.tileLayer` punta a `basemaps.cartocdn.com` → l'IP del visitatore esce comunque. Scritto com'è, non com'era
  comodo. Idem per `scriptplay.html`: `DEMO_MODE = true` e `OPENROUTER_KEY = ''` → nessuna chiamata AI in
  produzione, ma la nota spiega cosa cambia se l'operatore collega Ollama o una propria key.
- Aperto: tiles self-hosted, traduzione della notice (oggi solo EN su ~20 lingue), DPIA per i deployment reali → `goal.md`.

### open-wildguard-hub — sessione 2026-07-07c (chiusura buchi moduli + test critici)
- **M3 `tdoa_locate.py` chiude il loop:** aggiunto `--demo` + `--events`. Ora il fix del colpo di fucile emette **evento canonico** (`gunshot`, source acoustic) → entra in `wildguard.py`/`wg_store.py` come ogni altro detector. Confidence scala col residual (rms 0→1.0, 200 m→0.2): fix sporco = flaggato basso, ranger non insegue posizione sbagliata.
- **BUG M9 fixato (`case_file.py`):** evidence referenziata ma file **mancante** dal vault → prima `all_pass` restava True (PASS bugiardo in tribunale). Ora: file mancante con `--files-dir` = `all_pass=False`. Senza `--files-dir` = "NOT VERIFIED" neutro (non rompe uso offline). Semantica corretta per magistrato.
- **Test 34 → 54** (+20): `test_case_file.py` (integrità PASS/FAIL/missing, custody log, exit code court), `test_risk_model.py` (risk∈[0,1], hotspot>edge, **rotte imprevedibili** = seed diversi→rotte diverse, lunar bounded), TDoA event→pipeline. M9+M8 (court+patrol) ora coperti.
- **Copertura test: 5/14 → 8/14 moduli** (core field-critical tutti testati).

### open-wildguard-hub — sessione 2026-07-07b (SQLite store + export ricercatori)
- **`wg_store.py`** — event store single-file SQLite (stdlib `sqlite3`, zero install su clone). antirez-clean: 1 tabella, 1 file, apribile in QGIS/DB Browser/R/pandas. Ingest **idempotente** (no doppioni per event_id). Query per `--type`/`--since`/`--until`/`--min-conf`/`--near LAT LON --radius-km`. Risolve "JSON in cartella non scala" (query su 10k+ eventi).
- **Export ricercatori:** `--format csv|geojson|darwincore`. Darwin Core Occurrence = standard GBIF → una detection entra in un dataset di ricerca senza rework. GeoJSON per QGIS/Leaflet. CSV per R/pandas.
- **Wired nel runner:** `wildguard.py` popola auto `<out>/wildguard.sqlite` (fail-safe, non blocca il run). Flag `--db`.
- **Test 23 → 34** (`test_wg_store.py` +11: idempotenza, filtri spaziali/temporali, ordine lon,lat GeoJSON, termini DwC). `*.sqlite` in .gitignore.
- **goal.md ripulito (no entropy):** rimosso framing "M1 hub server = critical path/core blocker" (deprecato, deciso NO backend); event_schema ora "enforced"; Definition of Done riscritto offline-first.
- **Verdetto antirez:** core = stdlib single-clone, sempre-funziona, no dipendenze field-critical. ✅

### open-wildguard-hub — sessione 2026-07-07 (quality audit / production-ready)
- **BUG CRITICO FIXATO — `tdoa_locate.py`:** segno invertito nella linearizzazione Fang → fix del colpo di fucile ~6.5 km fuori posizione anche con input perfetto (verificato numericamente). Ora: 0 m esatto, 1 m con 2 ms di clock noise.
- **tdoa numpy rimosso** (era l'unica dipendenza del percorso field-critical): least-squares 3 incognite in stdlib (equazioni normali + eliminazione Gauss). Clone su Pi = zero pip.
- **tdoa 3-nodi funzionante:** sistema lineare sottodeterminato con 3 nodi → aggiunto raffinamento Gauss-Newton sulle equazioni nonlineari (2 incognite). Sub-metro da 3 nodi in su. Output `residual_rms_m` = spia di sync/coordinate sbagliate.
- **BUG FIXATO — `edge_infer_camera.py` zero-detection silenzioso:** default `--classes human vehicle` non matchava mai i nomi COCO (`person`, `car`...) → girava per sempre senza rilevare nulla. Ora: default weights `yolov8n.pt` (auto-download una volta, poi offline), `THREAT_MAP` label→threat_class canonico (person→intrusion, car/truck→vehicle = CASE_WORTHY), label grezza in metadata per audit court.
- **Test: 13 → 23, tutti verdi** (`test_tdoa_locate.py` 7, `test_edge_infer_camera.py` 3). Igiene: `report/`, `events/`, `evidence/` in .gitignore; requirements.txt aggiornato (M3 stdlib).
- **Prossimo:** firmware arduino ha TODO onesti (GPS timestamp, TFLite); M4 aerial resta design-only.

### open-wildguard-hub — sessione 2026-07-05 (offline runner)
- **Deciso: NIENTE backend esposto.** Il sito resta statico/offline; la gente clona il repo per usarlo. Il ruolo del "hub M0" (collegare i moduli) è fatto **offline, file-based, stdlib** da `wildguard.py`.
- **`toolkit/python/wildguard.py`** — runner: `events/*.json` → valida schema (rejects.json) → M5 enrich (opt, rete) → M8 risk grid+rotte → M9 case file+integrità SHA-256 → bundle (`SUMMARY.txt`, `manifest.json`). Trasforma 10 script-isola in 1 workflow. Exit≠0 su manomissione prove.
- **Integrazione reale provata:** `tip_intake`/`gps_geofence`/`node_health` `--demo --events` emettono eventi canonici che passano il runner (8 eventi, 0 scarti, 5 case file).
- **`toolkit/tests/test_wildguard.py`** — 13 test, tutti verdi, offline/stdlib.
- **`QUICKSTART.md`** — entry point operativo per chi clona.
- **Prossimo muro adozione:** M2/M3 non spediscono pesi modello → `fetch_models.py` + fallback no-model (da fare).

### open-wildguard-hub — milestone plan 2026-06-21
- **✅ `goal.md` riscritto con milestone tecniche** (M0–M6): FastAPI hub server, dashboard live binding, toolkit wiring (M2+M3), evidence viewer, risk heatmap, node monitor, use-cases docs. Ogni milestone ha: file esatti, schema SQL, API routes, test da scrivere, **dashboard expansion points** per agenti futuri. Priorità: M0→M2→M1→M3→M4→M5→M6.


