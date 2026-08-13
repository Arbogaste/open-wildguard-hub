/* Example dashboard — sample OSINT lead cards. Bundled sample output of osint_scrape.py.
   Loaded by demo.html only. */
        /* ---- M7 OSINT lead cards: render from Tactical Events (toolkit/python output) ---- */
        // Bundled sample (mirrors toolkit/data/sample_osint_leads.json). Same shape osint_scrape.py emits.
        // Store names + listing refs are masked on purpose (privacy / no live linking to listings).
        const OSINT_SAMPLE = [
            {evidence_url:"marketplace://listing/anon-7731",confidence:0.95,evidence_hash:"641ceb529a7e4f10b8d2a9c3e7f04a1b6d8c2e9f30a5b71c8e2f0d4a6b9c1e35",
             metadata:{title:"Antico avorio lavorato - white gold, no documenti",score:9,species_suspected:"ivory",price:"1.200,00 EUR",location_text:"Napoli",seller_contact:"+39 333 1234567",slang_terms_found:["white gold","avorio","no documenti"],source_site:"MarketPlace A",scraped_at_iso:"2026-06-21T03:42:11Z",needs_human_review:true,image:null}},
            {evidence_url:"classifieds://listing/anon-4420",confidence:0.78,evidence_hash:"a7b4f2188c0e6d31f95a2b7c4e8d019a3f6b2c8e1d4a709b5c3e6f1a2d8b4c70",
             metadata:{title:"Richiamo vivo da caccia - cardellino selvatico, senza permesso",score:7,species_suspected:"songbird",price:"80,00 EUR",location_text:"Foggia",seller_contact:"venditore_anon@example.com",slang_terms_found:["cardellino","richiamo vivo","selvatico","senza permesso"],source_site:"Classifieds B",scraped_at_iso:"2026-06-21T04:42:11Z",needs_human_review:true,image:null}},
            {evidence_url:"overseas-shop://listing/anon-9015",confidence:0.5,evidence_hash:"0d2f9a4c7e1b6835a0c4e8f2d6b9170c3a5e8f1b4d7092a6c8e0f3b5d1a7c920",
             metadata:{title:"Carved pendant - pangolin scale style, traditional",score:4,species_suspected:"pangolin",price:"$24.90",location_text:null,seller_contact:null,slang_terms_found:["artichoke"],source_site:"Overseas Shop C",scraped_at_iso:"2026-06-21T05:42:11Z",needs_human_review:true,image:null}}
        ];
        function listingRef(u){ const m=String(u||"").match(/anon-[\w]+/); return m?m[0]:"listing-redacted"; }
        const SPECIES_ICON = {ivory:"🐘",rhino_horn:"🦏",pangolin:"🦔",big_cat:"🐅",parrot:"🦜",songbird:"🐦",shark:"🦈",turtle:"🐢",generic:"⁉️"};
        function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c]));}
        function severity(sc){return sc>=8?"high":sc>=5?"med":"low";}
        function renderOsintLeads(events){
            const grid=document.getElementById('osint-leads-grid'); if(!grid)return;
            const rows=[...events].sort((a,b)=>(b.metadata.score||0)-(a.metadata.score||0));
            grid.innerHTML=rows.map(ev=>{
                const m=ev.metadata, sev=severity(m.score||0), ic=SPECIES_ICON[m.species_suspected]||"⁉️";
                const thumb=m.image?`style="background-image:url('${esc(m.image)}')"`:"";
                return `<div class="osint-card sev-${sev}">
                  <div class="osint-thumb" ${thumb}>${m.image?"":ic}</div>
                  <div class="osint-body">
                    <div class="osint-title">${esc(m.title)}</div>
                    <div class="osint-row"><span>Species</span><b>${esc(m.species_suspected||"?")}</b></div>
                    <div class="osint-row"><span>Price</span><b>${esc(m.price||"—")}</b></div>
                    <div class="osint-row"><span>Location</span><b>${esc(m.location_text||"—")}</b></div>
                    <div class="osint-row"><span>Site</span><b>${esc(m.source_site||"")}</b></div>
                    <div class="osint-slang">${(m.slang_terms_found||[]).map(t=>`<span class="osint-tag">${esc(t)}</span>`).join("")}</div>
                  </div>
                  <div class="osint-foot">
                    <span class="osint-score">SCORE ${m.score} · ${Math.round((ev.confidence||0)*100)}%</span>
                    <span class="osint-ref" title="Listing reference is masked. Full URL stays in the secure case file (M9), not on the public dashboard — naming a specific shop for a suspected crime is a legal/defamation risk.">ref ${esc(listingRef(ev.evidence_url))} 🔒</span>
                  </div>
                  <div class="osint-foot" style="border-top:none;padding-top:0">
                    <span class="osint-hash" title="SHA-256 evidence hash (chain of custody, M9)">sha256 ${esc((ev.evidence_hash||"").slice(0,18))}…</span>
                    ${m.needs_human_review?'<span class="osint-review">⚠ review</span>':""}
                  </div>
                </div>`;
            }).join("");
        }
        // Try the live file; fall back to the bundled sample (works under file://)
        (function loadOsint(){
            fetch('toolkit/data/sample_osint_leads.json').then(r=>r.ok?r.json():Promise.reject())
                .then(renderOsintLeads).catch(()=>renderOsintLeads(OSINT_SAMPLE));
        })();

