// HeroHealth Leaflet Map Handler

document.addEventListener('DOMContentLoaded', () => {
    // 1. Single Facility Detail Map
    const detailMapElement = document.getElementById('facilityDetailMap');
    if (detailMapElement) {
        const lat = parseFloat(detailMapElement.dataset.lat);
        const lon = parseFloat(detailMapElement.dataset.lon);
        const name = detailMapElement.dataset.name;
        const address = detailMapElement.dataset.address;

        const map = L.map('facilityDetailMap').setView([lat, lon], 15);

        // Dark-mode themed map tiles (CartoDB Dark Matter)
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 20
        }).addTo(map);

        // Red emergency marker or blue default marker
        const marker = L.marker([lat, lon]).addTo(map);
        marker.bindPopup(`<b>${name}</b><br><small>${address}</small>`).openPopup();
    }

    // 2. Full Search Map
    const fullMapElement = document.getElementById('searchMap');
    if (fullMapElement) {
        const specialty = fullMapElement.dataset.specialty || '';
        
        // Default Kathmandu coordinates
        const defaultLat = 27.700769;
        const defaultLon = 85.300140;

        const map = L.map('searchMap').setView([defaultLat, defaultLon], 12);

        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 20
        }).addTo(map);

        let userLocationMarker = null;
        let userCoords = null;

        // Try to fetch user current location
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    userCoords = [lat, lon];
                    
                    // Add a special green pulsing marker for user location
                    const userIcon = L.divIcon({
                        className: 'user-location-pulsing-icon',
                        html: '<div class="pulse-ring"></div><div class="pulse-dot"></div>',
                        iconSize: [20, 20]
                    });
                    
                    userLocationMarker = L.marker([lat, lon], { icon: userIcon }).addTo(map);
                    userLocationMarker.bindPopup("<b>Your Current Location</b>").openPopup();
                    
                    // Re-fetch and re-plot to include distances!
                    fetchAndPlotMarkers();
                },
                (err) => {
                    console.log("Geolocation permission denied or failed. Defaulting to Kathmandu.");
                    fetchAndPlotMarkers();
                }
            );
        } else {
            fetchAndPlotMarkers();
        }

        // Add custom styling for user pulsing icon
        const style = document.createElement('style');
        style.innerHTML = `
            .user-location-pulsing-icon {
                position: relative;
            }
            .pulse-ring {
                border: 3px solid var(--accent);
                -webkit-border-radius: 30px;
                height: 24px;
                width: 24px;
                position: absolute;
                left: -2px;
                top: -2px;
                animation: pulsate 1.8s ease-out infinite;
                opacity: 0.0;
            }
            .pulse-dot {
                background-color: var(--accent);
                height: 12px;
                width: 12px;
                border-radius: 50%;
                position: absolute;
                left: 4px;
                top: 4px;
                box-shadow: 0 0 10px var(--accent);
            }
            @keyframes pulsate {
                0% { transform: scale(0.1, 0.1); opacity: 0.0; }
                50% { opacity: 1.0; }
                100% { transform: scale(1.2, 1.2); opacity: 0.0; }
            }
        `;
        document.head.appendChild(style);

        // Fetch facilities from django GeoJSON API
        function fetchAndPlotMarkers() {
            let apiUri = '/facilities/api/geojson/';
            if (specialty) {
                apiUri += `?specialty=${encodeURIComponent(specialty)}`;
            }

            fetch(apiUri)
                .then(response => response.json())
                .then(data => {
                    const markersGroup = [];
                    
                    L.geoJSON(data, {
                        onEachFeature: (feature, layer) => {
                            const props = feature.properties;
                            const coords = feature.geometry.coordinates; // [lon, lat]
                            const lat = coords[1];
                            const lon = coords[0];
                            
                            let distanceText = '';
                            if (userCoords) {
                                const dist = getDistanceKm(userCoords[0], userCoords[1], lat, lon);
                                distanceText = `<br><span style="color:var(--accent); font-weight:700;">➔ ${dist.toFixed(2)} km away</span>`;
                            }

                            // Define status color tag
                            let statusColor = '#10b981'; // Available
                            if (props.status === 'Busy') statusColor = '#f59e0b';
                            else if (props.status === 'Emergency Only') statusColor = '#ef4444';

                            const popupHtml = `
                                <div style="min-width: 200px;">
                                    <h4 style="font-family: var(--font-heading); margin-bottom: 5px;">${props.name}</h4>
                                    <span style="font-size: 0.8rem; background: rgba(255,255,255,0.05); padding: 2px 8px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.1);">${props.type}</span>
                                    <span style="color:${statusColor}; font-weight:700; font-size:0.8rem; float:right;">● ${props.status}</span>
                                    <p style="margin: 8px 0; font-size: 0.85rem; color: var(--text-muted);">${props.address}</p>
                                    <p style="margin: 5px 0; font-size: 0.85rem;">📞 ${props.phone}</p>
                                    ${distanceText}
                                    <hr style="margin: 10px 0; border: 0; border-top: 1px solid rgba(255,255,255,0.1);">
                                    <a href="${props.detail_url}" class="nav-btn nav-btn-primary" style="display:block; text-align:center; padding: 4px; border-radius: 4px; font-size:0.8rem;">View Full Details</a>
                                </div>
                            `;
                            
                            layer.bindPopup(popupHtml);
                            markersGroup.push(layer);
                        }
                    }).addTo(map);

                    // Fit map bounds to show all markers if any exist
                    if (markersGroup.length > 0) {
                        const group = new L.featureGroup(markersGroup);
                        if (userLocationMarker) {
                            group.addLayer(userLocationMarker);
                        }
                        map.fitBounds(group.getBounds().pad(0.15));
                    }
                })
                .catch(err => console.error("Error loading facilities geojson:", err));
        }

        // Helper: Haversine distance formula in Km
        function getDistanceKm(lat1, lon1, lat2, lon2) {
            const R = 6371; // Radius of the earth in km
            const dLat = deg2rad(lat2 - lat1);
            const dLon = deg2rad(lon2 - lon1);
            const a =
                Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                Math.cos(deg2rad(lat1)) * Math.cos(deg2rad(lat2)) *
                Math.sin(dLon / 2) * Math.sin(dLon / 2);
            const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
            return R * c;
        }

        function deg2rad(deg) {
            return deg * (Math.PI / 180.0);
        }
    }
});
