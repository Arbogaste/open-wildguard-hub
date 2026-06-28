# M11–M20 — Environmental-Crime & Pollution Tier (DESIGN ONLY)

> Status: **design document, not implemented.** This is an *optional extension tier*, kept separate
> from the anti-poaching core (M1–M10) on purpose — no mixing of concerns. It reuses the same
> backbone (hub, canonical event, offline-first, hash chain of custody) so a team can adopt one
> pollution module without pulling in the rest.

## Why a separate tier

Wildlife crime and pollution crime are different *domains* but share the same *machinery*: a sensor
or an OSINT signal produces a timestamped, geolocated, hashed observation; an analyst reviews it; a
court-ready evidence package goes to the competent authority. The anti-poaching platform already
solves the machinery (M0 hub, `event_schema.json`, M9 custody, M7 OSINT, M8 prediction). The
pollution tier is **the same pipeline pointed at a different offence**, not a rewrite.

**Non-negotiables inherited from the core**
- Every observation normalizes to one canonical event (extend `event_schema.json` with a
  `domain` field: `wildlife` | `pollution`; add pollution `threat_class` values).
- Offline-first, hash-at-capture chain of custody (M9 applies unchanged).
- "Legally traceable" only: every module names the law it serves and the authority it reports to.
  No vigilante action — output is evidence for regulators/prosecutors.
- No naming a specific operator as guilty before adjudication (same defamation guardrail as M7).

## Architecture reuse map

| Core module | Reused by the pollution tier as |
|-------------|----------------------------------|
| M0 hub + schema | same ingestion, same map, same store (add `domain=pollution`) |
| M2 edge vision | open-burning plumes, slick detection, dump-site change detection |
| M3 bioacoustics | (limited) industrial-noise / chainsaw → deforestation overlap |
| M5 geofence | "exceedance inside a protected/sensitive zone" alerts |
| M7 OSINT | waste/e-waste trafficking ads, illegal-disposal offers |
| M8 prediction | exceedance-risk hotspots, inspection prioritisation |
| M9 forensics | the load-bearing piece — sampling chain of custody is stricter here |
| M10 resilience | node health for water/air probes |

---

## The modules

Each entry: **mission · field tiers · signals/sensors · legal hook · which core module it leans on.**

### M11 — Water Quality & Illegal Discharge
- **Mission:** detect illegal effluent into rivers/lakes — spikes in turbidity, pH, conductivity,
  dissolved oxygen, temperature, ammonia downstream of an outfall.
- **Tiers:** Essential = handheld probe + logbook → Intermediate = low-cost in-stream probe
  (pH/EC/turbidity/DO/temp) posting to hub → Advanced = sensor array + upstream/downstream delta.
- **Signals:** time-series exceedance vs. baseline + permit limit; sudden delta across an outfall.
- **Legal hook:** EU Water Framework Directive 2000/60/EC + Urban Waste Water Directive; US Clean
  Water Act (NPDES). Report to the river-basin / environmental agency.
- **Leans on:** M0, M8 (baseline + anomaly), M10 (probe health).

### M12 — Illegal Dumping & Toxic-Waste Sites
- **Mission:** find fly-tipping and unauthorised hazardous dumps; track growth of a site over time.
- **Tiers:** Essential = geotagged citizen photo → Intermediate = camera node + change detection →
  Advanced = repeat-pass satellite/drone change map.
- **Signals:** new pile detected, area growth, drum/container counts, leachate signature.
- **Legal hook:** EU Waste Framework Directive 2008/98/EC + Waste Shipment Regulation; US RCRA.
- **Leans on:** M2 (change detection), M6 (citizen tips), M9 (site evidence pack).

### M13 — Air Emissions & Open Burning
- **Mission:** detect illegal open burning of waste/plastics and abnormal stack emissions.
- **Tiers:** Essential = visual smoke log → Intermediate = low-cost PM2.5/PM10/CO/VOC node +
  thermal/visual plume detection → Advanced = dispersion model tying a plume back to a source.
- **Signals:** PM/VOC exceedance correlated with a detected plume and wind vector.
- **Legal hook:** EU Industrial Emissions Directive 2010/75/EU + Ambient Air Quality 2008/50/EC;
  US Clean Air Act. Report to air-quality authority.
- **Leans on:** M2 (plume CV), M8 (dispersion/source attribution as a risk layer).

### M14 — Soil & Groundwater Contamination
- **Mission:** record contamination evidence (heavy metals, hydrocarbons) with sampling provenance.
- **Tiers:** Essential = sample + lab result logged with GPS/photo → Intermediate = structured
  sampling campaign with QA/QC → Advanced = contamination-plume mapping over monitoring wells.
- **Signals:** lab exceedance vs. regulatory threshold, tied to a custody-tracked sample.
- **Legal hook:** EU Environmental Liability Directive 2004/35/EC; US CERCLA/Superfund.
- **Leans on:** M9 (sample chain of custody is the core deliverable here).

### M15 — Marine Pollution & Oil Spills
- **Mission:** detect slicks, bilge dumping, and coastal discharge.
- **Tiers:** Essential = sighting report → Intermediate = coastal camera + slick CV + AIS vessel
  correlation → Advanced = SAR satellite slick detection tied to vessel track.
- **Signals:** slick detected + nearest AIS track + time window.
- **Legal hook:** MARPOL Annex I; EU Directive 2005/35/EC on ship-source pollution; national coast
  guard. **Vessel correlation is a lead, not proof** — same naming guardrail as M7.
- **Leans on:** M2 (slick CV), M4 (geo/satellite), M8.

### M16 — Deforestation & Illegal Land-Use Change
- **Mission:** detect unauthorised clearing/logging via repeat-pass satellite change.
- **Tiers:** Essential = ranger report → Intermediate = NDVI change alerts on a parcel watchlist →
  Advanced = near-real-time forest-loss alerts cross-referenced with permits.
- **Signals:** vegetation loss inside a protected/permit-restricted polygon.
- **Legal hook:** EU Deforestation Regulation (EUDR) 2023/1115; national forestry codes.
- **Leans on:** M4 (Sentinel-2/NDVI — shares the unbuilt M4 geo stack), M5 (parcel geofence).

### M17 — Mining & Quarry Runoff
- **Mission:** detect acid mine drainage and sediment runoff from (illegal) extraction.
- **Tiers:** Essential = downstream probe → Intermediate = pH/metals/turbidity array + visual
  sediment plume → Advanced = source attribution along the watershed.
- **Signals:** low pH + dissolved-metals + turbidity downstream of a site.
- **Legal hook:** national mining/water law; EU Mining Waste Directive 2006/21/EC.
- **Leans on:** M11 (shares water-probe stack), M2, M8.

### M18 — E-Waste & Hazardous-Material Trafficking (OSINT)
- **Mission:** detect illegal trade/disposal of e-waste, batteries, refrigerants, asbestos, ozone-
  depleting substances — online and at border/transfer points.
- **Tiers:** Essential = manual marketplace search → Intermediate = the M7 scraper pointed at a
  hazardous-material slang dictionary → Advanced = shipment/manifest cross-reference.
- **Signals:** listing/offer matching a hazardous-material dictionary; mismatched waste codes.
- **Legal hook:** Basel Convention; EU Waste Shipment Regulation; F-gas Regulation.
- **Leans on:** **M7 directly** — add a `hazmat` dictionary to `slang_dict.json`, reuse
  `osint_scrape.py` and `osint_sites.json` unchanged.

### M19 — Agro-chemical & Pesticide Misuse
- **Mission:** flag use/sale of banned pesticides and runoff into watercourses.
- **Tiers:** Essential = field report + product photo → Intermediate = OSINT on banned-product
  sales + downstream water probe → Advanced = residue sampling campaign.
- **Signals:** banned active-ingredient listing; pesticide signature in M11 water data.
- **Legal hook:** EU Regulation 1107/2009 + banned-substance lists; Rotterdam Convention.
- **Leans on:** M7 (sales), M11 (water), M9 (residue samples).

### M20 — Pollution Evidence, Custody & Regulatory Reporting
- **Mission:** the M9 analogue for pollution — turn observations + lab results into a regulator-
  ready package with unbroken sampling provenance and the correct legal citations.
- **Tiers:** Essential = hash manifest + custody log → Intermediate = templated regulatory report
  (auto-cite the applicable directive/permit) → Advanced = direct submission workflow + chain to
  cross-border authority (Basel/INTERPOL Environmental Crime).
- **Signals:** n/a — this is the packaging/compliance layer.
- **Legal hook:** EU Environmental Crime Directive 2024/1203; INTERPOL Pollution Crime WG; national
  EPA equivalents.
- **Leans on:** **M9 directly** (extend `case_file.py` with pollution citation templates + sampling
  QA/QC fields). This is the highest-value first build of the tier.

---

## Schema delta (when/if built)

Minimal, additive — does not break M1–M10:

```
event.domain        : "wildlife" | "pollution"          (default "wildlife")
event.threat_class  : + "effluent_exceedance" | "illegal_dump" | "open_burning"
                        | "oil_slick" | "deforestation" | "mine_runoff"
                        | "hazmat_listing" | "pesticide_misuse" | ...
event.metadata      : domain-specific (parameter, value, unit, threshold, permit_id,
                        sample_id, lab_method, qa_qc, exceedance_pct, ...)
```

## Build order (if the project decides to proceed — NOT now)

1. **M20** evidence/custody + **M11** water (highest legal leverage, smallest sensor cost).
2. **M18** e-waste OSINT (almost free — reuses M7 with a new dictionary).
3. **M12 / M13** dumping & open burning (reuse M2 change-detection / CV).
4. **M16 / M17 / M15** geo-heavy (gated on the still-unbuilt M4 satellite stack).
5. **M14 / M19** sampling-campaign modules (depend on M20 custody being solid).

> Reminder: this document is **design only**. No code, no toolkit scripts, no hub changes have been
> made for M11–M20. Implement only after the core (M0 hub especially) is live.
