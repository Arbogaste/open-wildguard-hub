# WildGuard AI — changelog sessioni

> Storico tecnico, una voce per sessione. Cosa manca e perché → `README.md` e `docs/FIELD-NEEDS.md`.
> Piano milestone → `PLAN.md`. 

### open-wildguard-hub — sessione 2026-08-13b (onestà del sito: via i numeri finti)
- **Header**: "SYSTEM ONLINE" era una bugia (nessun sensore collegato) → `DEMO — SAMPLE DATA`. Sottotitolo:
  "documentation site, not a live system".
- **Colonna sinistra rifatta**: "Telemetria Sensori" con 12 cam trap / 8 nodi audio / 34 collari / 1.4K OSINT
  (numeri inventati) → **"What you get when you clone"** con numeri verificabili nel repo (14 script, 54 test,
  0 server, €0/anno). I due allarmi mock ("Rilevamento Umano Armato, CONF 94%") → pannello **"Run it yourself"**
  con il comando e **l'output reale** di `wildguard.py --demo`, copiato da un'esecuzione vera.
- **Bug di onestà**: `triggerSimAlert()` incrementava il contatore camera trap ad ogni click. Ora scrive in un
  `#sim-log` etichettato sotto la mappa e non tocca i contatori — che descrivono il repo, non una rete di sensori.
- **Mappa**: nota esplicita che scenario, stazioni e allarmi sono sintetici, generati nel browser.
- **Claim gonfiati rimossi**: "riduce del 90% i falsi allarmi" (mai misurato), "Alert in 30s", "TDoA in <30s",
  "20+ repos integrated" → affermazioni verificabili (14 script, 54 test, 30 repo esaminati, residual_rms_m).
- **Tab Toolkit**: ogni riga `out` ora è output reale di `--demo`, non scritto a mano (M8 era 0.94, reale 0.89;
  species_lookup mostrava una GBIF key non verificata). Aggiunte righe runner + event store; M2 dichiara di non
  spedire pesi invece di dirsi pronto.
- **Tab OSINT**: da vetrina di card a spiegazione concreta — cosa fa la regola, output reale del `--demo`, e il
  limite dichiarato (74 termini contro 4.000 del benchmark) con link alla pagina organizzazioni.

- Nuovi target interni: duplicazione stringhe i18n (inline + JSON), mappa che carichi `events.json` vero.

### open-wildguard-hub — sessione 2026-08-13 (field needs, pagina organizzazioni, pulizia docs)
- **`docs/FIELD-NEEDS.md`** (nuovo, fonte unica): 13 organizzazioni anti-bracconaggio reali censite dalle loro
  pagine pubbliche (Patrol, Protrack, Big Life, Panthera, Thula Thula, GCF, Global Guardians, ADI, IWC, IFAW,
  LIFE WolfAlps, Sea Shepherd, BMUKN) + cosa dichiarano di servirgli + sezione **Where to donate** (indice
  verificato: unità ranger, famiglie dei ranger, wildlife crime, specie, marino, Europa). Il progetto non
  accetta donazioni: dichiarato esplicitamente.
- **`organizations.html`** (nuovo): vista sul markdown con lo stesso renderer di `readme.html` — zero copia del
  contenuto. Linkata da index (footer + nav strip + start-here), readme, scriptplay, privacy, sitemap, `sw.js`.
- **`README.md` sgrassato**: rimosse Roadmap / Immediate Priorities / Current Build Focus / Production Readiness. 
Sostituite
  da un puntatore unico. Aggiunte righe `wildguard.py` + `wg_store.py` in "What runs today".
- **`index.html`**: blocco "Start here" con 5 percorsi lettore, cluster repo "Training data & pretrained weights"
  (dataset con classe `Poacher`, elefanti aerei ~4.9k, TFLite per MCU, anomalie collari), passata i18n generica
  `[data-i18n]` con innerHTML.
- **`repo_index.md`** (workspace): schede 26–30 per i 5 repo nuovi + righe nella matrice moduli.
- Fix: `scriptplay.html` aveva un `</div>` in eccesso dentro `<main>`; rimosso senza cambiare il DOM renderizzato.
  `sw.js` v2 → v3, precache di `readme.html`, `README.md`, `organizations.html`, `docs/FIELD-NEEDS.md`.
- 54 test verdi, 5 pagine con tag bilanciati, sitemap valida.

### open-wildguard-hub — sessione 2026-08-03 (privacy notice del sito pubblico)
- **`privacy.html`** (EN, standalone, palette del hub): titolare = maintainer del progetto, log hosting Vercel,
  `localStorage` (`wildguard_lang`), tiles CARTO come terza parte, nessun cookie/analytics/ads, diritti + Garante.
  Linkata da `index.html` (footer credits), `readme.html` (header), `scriptplay.html` (header).
- **Verifica sul codice, non sulle intenzioni**: il commento in `index.html` dice "Leaflet self-hosted", ma
  `L.tileLayer` punta a `basemaps.cartocdn.com` → l'IP del visitatore esce comunque. Scritto com'è, non com'era
  comodo. Idem per `scriptplay.html`: `DEMO_MODE = true` e `OPENROUTER_KEY = ''` → nessuna chiamata AI in
  produzione, ma la nota spiega cosa cambia se l'operatore collega Ollama o una propria key.
- Aperto: tiles self-hosted, traduzione della notice (oggi solo EN su ~20 lingue), DPIA per i deployment reali.

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
- **Obiettivi ripuliti (no entropy):** rimosso framing "M1 hub server = critical path/core blocker" (deprecato, deciso NO backend); event_schema ora "enforced"; Definition of Done riscritto offline-first.
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
- **✅ Milestone tecniche riscritte** (M0–M6): FastAPI hub server, dashboard live binding, toolkit wiring (M2+M3), evidence viewer, risk heatmap, node monitor, use-cases docs. Ogni milestone ha: file esatti, schema SQL, API routes, test da scrivere, **dashboard expansion points** per agenti futuri. Priorità: M0→M2→M1→M3→M4→M5→M6.


