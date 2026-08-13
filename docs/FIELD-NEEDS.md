# Field Needs — what real anti-poaching organizations actually ask for

This page exists because a tool built without listening to the field is a demo, not a product.

Below is a survey of organizations that do anti-poaching work today: what each one does, and what they say
they need. Everything here comes from their own public pages, linked at each entry. Nothing is inferred
from marketing copy, and no organization listed here has endorsed, funded, or reviewed this project.

At the end, the needs are turned into concrete work items. Each one is open work: if you want to
help, start there.

**If you work at one of these organizations and we got you wrong, open an issue.** That correction is worth
more to us than a new feature.

---

## The organizations

### Patrol — informant network operations
Anti-poaching operations across Botswana, Cameroon, Mozambique, Namibia, South Africa, Tanzania, Uganda,
Zambia, Zimbabwe. Combines ranger patrols with community informant networks, aerial and river support.

What they say they need:

- **Handler continuity.** "When the handler changes, the network must be rebuilt almost from scratch."
  Intelligence lives in one person's head and dies when that person leaves.
- **Informant protection.** Being identified as an informant carries real physical risk; relocation is a
  budget line, not an edge case.
- **Tip verification.** A single clean-looking report can be deliberate misinformation planted to pull
  patrols away from the real target.
- **Countering encrypted coordination.** Poaching groups coordinate on encrypted messaging; patrols do not
  have a symmetric capability.

Source: https://www.patrolling.org/the-informant-network-system/

### Protrack Anti-Poaching Unit — private ranger unit, Limpopo, South Africa
One of the oldest private APUs, based in Hoedspruit near the Greater Kruger. Field teams on a six-week
training programme, K9 units (Belgian Malinois, Bloodhounds), helicopter support for Big Five reserves,
monthly intelligence reporting on game counts and incident locations.

Equipment in use: thermal and night vision, surveillance drones, tracking and listening devices, advanced
comms. Stated needs are ranger salaries, K9 upkeep, equipment, and intelligence gathering — recurring
operating cost, not software.

Sources: https://protrackapu.co.za/services/introduction-to-anti-poaching-services/ ·
https://protrackapu.co.za/protrack-rhino-task-team/ ·
https://protrackapu.co.za/training/anti-poaching-training-course/

### Big Life Foundation — Greater Amboseli, Kenya and Tanzania
390 rangers, 46 ranger units, 32 permanent outposts, 12 mobile units. Daily foot and vehicle patrols,
field camera monitoring, night-vision and GPS technology, community informant networks, tracker dogs, and
direct support to wildlife-crime prosecutions with local prosecutors.

Source: https://biglife.org/what-we-do/wildlife-protection/anti-poaching

### Panthera — big cats, global
Anti-poaching teams in 12 core areas, 300+ rangers trained. Runs acoustic monitors that record gunshots to
predict poaching patterns (Guatemala, Honduras) and **PoacherCam**, a camera trap with an on-device
human-detection algorithm that alerts patrols to intruders. Analyses law enforcement data jointly with
governments, communities and other NGOs.

This is the closest existing system to what M2 and M3 do. The difference we can offer is not capability —
it is that ours is open, forkable, and free.

Source: https://panthera.org/threat-poaching

### Thula Thula — private reserve, KwaZulu-Natal, South Africa
24/7 protection unit on a single reserve. Bush trap cameras that push images in real time to the security
team, fence patrols, snare removal, K9 tracker teams, dedicated rhino monitoring, response teams for
ambush operations. Two bases after a land expansion, to cut response time.

The archetype of the small operator this project is designed for: no IT department, no budget for a
platform, real need for one.

Source: https://thulathula.com/conservation/wildlife-protection-anti-poaching/

### Global Conservation Force — training and K9, USA-based
Ranger training courses, embedded response teams, K9 units. Their published needs list is unusually
concrete: boots, backpacks, compasses, radios, GPS units, first aid kits, night vision, bump helmets,
bulletproof vests, K9 harnesses and bite suits, veterinary cover for the dogs.

Note what is not on that list: software. Any tool that asks these teams for a subscription is asking them
to choose between it and boots.

Source: https://globalconservationforce.org/anti-poaching/

### Global Guardians Conservation Fund — ranger training pipeline, Australia
Anti-poaching training programmes (10-day to 6-week), firearms training, and ranger placement into
employment after training. Funds conservation work and connects volunteers.

Relevant need: **trained personnel, and continuity from training into deployment.** A tool that a newly
placed ranger can learn in an afternoon has a distribution channel here.

Source: https://gguardians.org/

### José & Liso Anti-Poaching Fund (Animal Defenders International) — sanctuary security
Created after two rescued lions were killed at a sanctuary in Limpopo. Funds armed guards, electronic
security (lights and sensors), specialist investigators working with law enforcement, and explicitly
**geospatial and crime pattern analysis**.

Sanctuaries are a distinct threat model: fixed perimeter, known animals, attacks that are targeted rather
than opportunistic.

Source: https://antipoachingfund.org/

### International Wildlife Crimestoppers — North America
Non-profit founded by wildlife resources officers. Information sharing between anti-poaching agencies,
public education on lawful vs illegal harvesting, funding for enforcement equipment, and a cash reward
programme for major cases. Runs a public "Report A Poacher" channel.

Relevant need: **anonymous public reporting that survives cross-agency handoff**, and reward accounting
tied to a case without exposing the reporter.

Source: https://wildlifecrimestoppers.org/

### IFAW — Coalition to End Wildlife Trafficking Online
Launched in 2018 with WWF and TRAFFIC, now 50+ technology companies. Members have blocked or removed over
24.1 million prohibited wildlife listings and suspected illicit sellers. The coalition maintains a database
of **4,000+ search terms** used in illegal trade, has trained 3,000+ company staff in detection, and
receives tens of thousands of volunteer reports.

This is the direct benchmark for M7. Our slang dictionary currently holds 74 terms.

Source: https://www.ifaw.org/international/journal/working-together-stop-wildlife-trafficking-online

### LIFE WolfAlps EU — poisoning, Alpine region
EU LIFE project covering the whole Alpine arc, including Italy. Poaching is among the largest causes of
wolf mortality. The core method being countered is **poisoned bait**, which also kills scavengers and
other non-target wildlife, and is a public-health risk. Counter-measures are anti-poison dog units,
forensic and judicial coordination, and public awareness.

The nearest field reality to this project's own home region, and the one method our event schema cannot
currently express.

Source: https://www.lifewolfalps.eu/en/axes-of-intervention/antibracconaggio/

### Sea Shepherd — marine poaching and IUU fishing
Direct-action patrols against illegal fishing and marine wildlife killing: vaquita refuge patrols in the
Gulf of California, Scorpion Reef, illegal driftnets, Antarctic krill trawling, removal of tens of
thousands of illegal octopus traps in Greece.

Marine is out of scope for this repo today. It is listed because the pattern — patrol, evidence, chain of
custody, prosecution — is the same, and because AIS vessel data is an open dataset an M4 tier could use.

Source: https://seashepherd.org/

### German Federal Environment Ministry (BMUKN) — institutional funding
About €4 million per year for anti-poaching in Africa and Asia, including €9.7 million (2025–2029) for the
Partnership against Wildlife Crime, and long-running support to the African Elephant Fund.

The capacity gaps they fund are revealing, because they are not about sensors: training prosecutors and
judges, cooperation between police, customs and judiciary across borders, financial investigation to trace
proceeds, and anti-corruption strategies inside enforcement agencies.

Source: https://www.bundesumweltministerium.de/en/topics/species-protection/international-species-protection/combatting-poaching

---

## What this survey changes in the project

Six things recur across organizations that otherwise have nothing in common. Each is now open work on
this repo, listed here rather than buried in a tracker.

**1. They already have a data standard, and it is not ours.** Most funded ranger operations record patrols
in SMART Conservation Tools. Asking them to adopt WildGuard currently means asking them to abandon their
patrol history. An import/export path is worth more than any new detector.

**2. Poisoning is a first-class method, and we cannot log it.** LIFE WolfAlps is built around poisoned bait;
vulture and big-cat poisoning is widespread in Africa. Our event schema has no class for it, so an
anti-poison dog unit has nothing to record.

**3. Tips are adversarial.** Patrol states plainly that a plausible tip can be planted misinformation, and
that a network collapses when its handler leaves. Our tip intake protects the source but assumes the
content is honest and that the handler is permanent. Both assumptions are wrong.

**4. A stopped animal is the alarm.** Big Life, Panthera and every collar operator care less about an
animal crossing a line than about an animal that stopped moving. We built the geofence and skipped the
anomaly.

**5. Online trade monitoring needs vocabulary at scale.** 74 slang terms against a 4,000-term industry
benchmark. The gap is not code, it is a contribution path plus provenance for each term so a match can be
defended in a report.

**6. Zero recurring cost is the actual feature.** These organizations buy boots, radios and dog food. Every
euro of software subscription is a euro not spent on a ranger. That is why this repo has no paid API on the
critical path, no license, and no server to rent — and why that constraint is non-negotiable rather than a
nice-to-have.

One more finding sits outside the toolkit entirely. The largest institutional funder in this list spends
its money on prosecutors, customs cooperation, financial investigation and anti-corruption — not on
sensors. The bottleneck between a detection and a conviction is legal, not technical. That is the reason
M9 exists, and the reason a case file that a prosecutor accepts matters more than a better model.

---

## Where to donate

**This project does not accept donations and has nothing to sell.** No account, no license, no
"pro tier", no wallet address. If a page claiming to be WildGuard AI asks you for money, it is not us.

What we can do is point you at the people who need the money. Everything below is field work — rangers,
dogs, fuel, radios, court cases, ranger families. Verify each organization yourself before giving; we
have no relationship with any of them and receive nothing from these links.

Ranger units and reserve protection:

- **Big Life Foundation** — 390 rangers across the Greater Amboseli, Kenya and Tanzania. https://biglife.org/
- **Panthera** — big-cat anti-poaching teams, acoustic monitoring, PoacherCam. https://panthera.org/
- **Global Conservation Force** — ranger training, K9 units, and a published gear list. https://globalconservationforce.org/
- **Protrack Anti-Poaching Unit** — private APU near the Greater Kruger; funds salaries and K9 upkeep. https://protrackapu.co.za/
- **Thula Thula / South African Conservation Fund** — single-reserve unit, rhino monitoring, K9. https://thulathula.com/
- **José & Liso Anti-Poaching Fund (ADI)** — sanctuary security and poaching investigations. https://antipoachingfund.org/
- **Global Guardians Conservation Fund** — training rangers and placing them into work. https://gguardians.org/

Rangers themselves, and their families:

- **The Thin Green Line Foundation** — supports the families of rangers killed on duty. https://www.thingreenline.org.au/
- **Game Rangers Association of Africa** — professional body for African rangers. https://www.gameranger.org/

Wildlife crime, trafficking and demand reduction:

- **IFAW** — runs the Coalition to End Wildlife Trafficking Online. https://www.ifaw.org/
- **TRAFFIC** — the wildlife trade monitoring network. https://www.traffic.org/
- **WildAid** — demand reduction and marine enforcement. https://www.wildaid.org/
- **WWF** — large-scale programmes; pick your national office. https://www.worldwildlife.org/
- **International Wildlife Crimestoppers** — North America; enforcement equipment and reward fund. https://wildlifecrimestoppers.org/

Species and habitat programmes:

- **Save the Elephants** — tracking, research and anti-poaching in Kenya. https://www.savetheelephants.org/
- **International Rhino Foundation** — rhino protection across Africa and Asia. https://rhinos.org/

Marine:

- **Sea Shepherd** — direct-action patrols against illegal fishing and marine poaching. https://seashepherd.org/

Europe:

- **LIFE WolfAlps EU** — anti-poison dog units and anti-poaching across the Alps. Publicly co-funded rather than donation-driven; the useful contribution here is reporting poisoned bait to the project or to local authorities. https://www.lifewolfalps.eu/

If you want to support this repository instead, the currency is not money: test it in the field, report
what breaks, correct a fact, translate a page, or contribute a term to the slang dictionary. See
`../CONTRIBUTING.md`.

---

## How to reach us

If you run one of these operations, or one like it: the fastest way to make this project useful is to tell
us what breaks when you try it. Open an issue at
https://github.com/Arbogaste/open-wildguard-hub/issues — including "this is the wrong tool for us, here is
why". That is a valid and useful issue.
