/* Example dashboard — map, patrol routing and simulated alerts.
   Synthetic data only. Loaded by demo.html; deliberately NOT loaded by index.html. */
        // Init Map of Serengeti-like park area (mocked coordinates)
        const centerCoords = [-2.35, 34.83];
        const map = L.map('map', {
            zoomControl: true,
            attributionControl: false
        }).setView(centerCoords, 12);

        // Dark-mode tactical map tiles. Online: CartoCDN dark basemap.
        // Offline-first: failed tiles fall back to a local dark placeholder so the
        // command center (markers, routes, overlays) stays usable with no network.
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            maxZoom: 20,
            errorTileUrl: 'vendor/leaflet/tile-offline.png',
            crossOrigin: true
        }).addTo(map);

        // Layer groups for dynamic controls
        const markerLayer = L.layerGroup().addTo(map);
        const routeLayer = L.layerGroup().addTo(map);

        // Core data
        const rangerStations = [
            { name: "Stazione Nord", coords: [-2.312, 34.821] },
            { name: "Stazione Sud", coords: [-2.385, 34.851] },
            { name: "Posto di Controllo Ovest", coords: [-2.348, 34.789] }
        ];

        // Draw initial ranger stations
        rangerStations.forEach(station => {
            L.marker(station.coords, {
                icon: L.divIcon({
                    html: ``,
                    className: 'custom-icon',
                    iconSize: [20, 20]
                })
            }).bindPopup(`<b>${station.name}</b><br>Stazione Ranger`).addTo(markerLayer);
        });

        // Time ticker helper
        function updateTime() {
            const now = new Date();
            document.getElementById('tactical-time').innerText = now.toUTCString().replace("GMT", "UTC");
        }
        setInterval(updateTime, 1000);
        updateTime();

        // Dispatch ranger action (Dijkstra simulation)
        function dispatchRanger(lat, lon, sensorId) {
            routeLayer.clearLayers();
            const lang = translations[currentLanguage];

            // Draw threat point
            const threatMarker = L.marker([lat, lon], {
                icon: L.divIcon({
                    html: ``,
                    className: 'custom-icon',
                    iconSize: [25, 25]
                })
            }).addTo(routeLayer);

            // Find "nearest" station (Simple Euclidean distance mock Dijkstra)
            let nearestStation = rangerStations[0];
            let minDist = Infinity;
            rangerStations.forEach(s => {
                let d = Math.sqrt(Math.pow(s.coords[0] - lat, 2) + Math.pow(s.coords[1] - lon, 2));
                if (d < minDist) {
                    minDist = d;
                    nearestStation = s;
                }
            });

            // Draw line simulating shortest path route
            const route = L.polyline([nearestStation.coords, [lat, lon]], {
                color: '#00ff66',
                weight: 3,
                dashArray: '5, 10',
                opacity: 0.8
            }).addTo(routeLayer);

            map.fitBounds(route.getBounds(), { padding: [50, 50] });

            alert(`${lang.alert_dispatch}${sensorId} (${nearestStation.name}).`);
        }

        // Simulate edge alert
        function triggerSimAlert() {
            const randomLat = centerCoords[0] + (Math.random() - 0.5) * 0.08;
            const randomLon = centerCoords[1] + (Math.random() - 0.5) * 0.08;
            const log = document.getElementById('sim-log');
            const alertId = 'alert-' + Date.now();
            const lang = translations[currentLanguage];

            const alertHtml = `
                <div class="alert-item critical" id="${alertId}">
                    <div class="alert-meta">
                        <span>CAMERA_EDGE_SIM</span>
                        <span>${currentLanguage === 'it' ? 'Tempo Reale' : 'Realtime'}</span>
                    </div>
                    <div class="alert-desc">${currentLanguage === 'it' ? 'Rilevamento Sospetto Intruso' : 'Suspicious Intruder Detected'}</div>
                    <div class="alert-footer">
                        <span class="badge" style="color: var(--color-danger); border-color: rgba(255, 51, 68, 0.2);">CONF: 91%</span>
                        <button class="btn btn-danger" onclick="dispatchRanger(${randomLat}, ${randomLon}, 'CAMERA_EDGE_SIM')">${lang.btn_dispatch}</button>
                    </div>
                </div>
            `;
            log.insertAdjacentHTML('afterbegin', alertHtml);
            // Deliberately does not touch the counters on the left: those describe the repository,
            // not a sensor network, and a simulated click must never inflate them.

            // Mark on map
            L.marker([randomLat, randomLon], {
                icon: L.divIcon({
                    html: ``,
                    className: 'custom-icon-alert',
                    iconSize: [20, 20]
                })
            }).addTo(routeLayer).bindPopup(`<b>${currentLanguage === 'it' ? 'Allarme Intrusione' : 'Intrusion Alert'}</b>`).openPopup();
        }

        // Calculate Minimum Spanning Tree patrol path for all stations
        function calculatePatrolRoute() {
            routeLayer.clearLayers();
            const lang = translations[currentLanguage];

            const points = rangerStations.map(s => s.coords);
            const polyline = L.polygon(points, {
                color: '#00bcd4',
                fillColor: '#00bcd4',
                fillOpacity: 0.05,
                weight: 2
            }).addTo(routeLayer);

            map.fitBounds(polyline.getBounds(), { padding: [50, 50] });
            alert(lang.alert_route_calculated);
        }

        // Generate legal document chargesheet
        function generateChargesheet(specie, reato, sezioni) {
            const box = document.getElementById('chargesheet-output');
            const content = document.getElementById('chargesheet-text');
            const now = new Date();
            const lang = translations[currentLanguage];

            const template = `${currentLanguage === 'it' ? 'VERBALE DI REPARTO FORENSE' : 'FORENSIC INCIDENT REPORT'} // CITES & WPA COMPLIANT
--------------------------------------------------
${currentLanguage === 'it' ? 'DATA DI REDAZIONE' : 'REPORT DATE'}: ${now.toLocaleDateString()} ${now.toLocaleTimeString()}
${currentLanguage === 'it' ? 'GIURISDIZIONE' : 'JURISDICTION'}: Forestry Territorial Office - Reserve Division

${currentLanguage === 'it' ? "CAPO D'ACCUSA" : 'ACCUSATION'}:
Wildlife Protection Act Violation.
${currentLanguage === 'it' ? 'SPECIE COINVOLTA' : 'INVOLVED SPECIES'}: ${specie} (Ref. Schedules WPA)
${currentLanguage === 'it' ? 'TIPO DI REATO' : 'OFFENSE TYPE'}: ${reato}
${currentLanguage === 'it' ? 'SEZIONI APPLICATE' : 'APPLIED SECTIONS'}: WPA 1972, ${sezioni}

${currentLanguage === 'it' ? 'STATO DELLE PROVE' : 'EVIDENCE STATUS'}:
- Original media files securely archived in local vault.
- SHA-256 generated and appended to local immutable hash chain.
- Integrity verification: OK.

Forest Officer Authorized Signature
--------------------------------------------------`;

            content.innerText = template;
            box.style.display = 'block';
        }

        function copyChargesheet() {
            const text = document.getElementById('chargesheet-text').innerText;
            navigator.clipboard.writeText(text);
            alert(currentLanguage === 'it' ? "Verbale legale copiato negli appunti." : "Legal writ copied to clipboard.");
        }

        function clearMapLayers() {
            routeLayer.clearLayers();
        }


