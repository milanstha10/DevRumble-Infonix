document.addEventListener('DOMContentLoaded', function () {
    const detailMapElement = document.getElementById('facilityDetailMap');

    if (detailMapElement && typeof L !== 'undefined') {
        const lat = parseFloat(detailMapElement.dataset.lat);
        const lon = parseFloat(detailMapElement.dataset.lon);
        const name = detailMapElement.dataset.name || 'Healthcare Facility';
        const address = detailMapElement.dataset.address || '';

        if (Number.isFinite(lat) && Number.isFinite(lon)) {
            const detailMap = L.map('facilityDetailMap').setView([lat, lon], 15);

            L.tileLayer(
                'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
                {
                    attribution:
                        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
                    subdomains: 'abcd',
                    maxZoom: 20
                }
            ).addTo(detailMap);

            const marker = L.marker([lat, lon]).addTo(detailMap);

            marker.bindPopup(
                `<strong>${escapeHtml(name)}</strong><br><small>${escapeHtml(address)}</small>`
            ).openPopup();

            setTimeout(function () {
                detailMap.invalidateSize();
            }, 200);
        }
    }

    const fullMapElement = document.getElementById('searchMap');

    if (!fullMapElement) {
        return;
    }

    if (typeof L === 'undefined') {
        console.error('Leaflet is not loaded.');
        return;
    }

    const specialty = fullMapElement.dataset.specialty || '';
    const loadingElement = document.getElementById('mapLoading');

    const defaultLat = 27.700769;
    const defaultLon = 85.300140;

    let map;

    try {
        map = L.map('searchMap', {
            center: [defaultLat, defaultLon],
            zoom: 12,
            zoomControl: true
        });
    } catch (error) {
        console.error('Unable to initialize Leaflet map:', error);

        if (loadingElement) {
            loadingElement.innerHTML =
                '<i class="fa-solid fa-circle-exclamation"></i> Unable to initialize map.';
        }

        return;
    }

    L.tileLayer(
        'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
        {
            attribution:
                '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 20
        }
    ).addTo(map);

    let userLocationMarker = null;
    let userCoords = null;
    let facilitiesLayer = null;

    const userIcon = L.divIcon({
        className: 'user-location-pulsing-icon',
        html: '<div class="pulse-ring"></div><div class="pulse-dot"></div>',
        iconSize: [20, 20],
        iconAnchor: [10, 10]
    });

    function showLoading() {
        if (loadingElement) {
            loadingElement.classList.remove('hidden');
        }
    }

    function hideLoading() {
        if (loadingElement) {
            loadingElement.classList.add('hidden');
        }
    }

    function showError(message) {
        if (loadingElement) {
            loadingElement.classList.remove('hidden');
            loadingElement.innerHTML =
                `<i class="fa-solid fa-circle-exclamation"></i> ${escapeHtml(message)}`;
        }
    }

    function getApiUrl() {
        const baseUrl = '/facilities/api/geojson/';

        if (!specialty) {
            return baseUrl;
        }

        return `${baseUrl}?specialty=${encodeURIComponent(specialty)}`;
    }

    async function fetchAndPlotMarkers() {
        showLoading();

        try {
            const response = await fetch(getApiUrl(), {
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error(`API returned HTTP ${response.status}`);
            }

            const data = await response.json();

            if (!data || data.type !== 'FeatureCollection') {
                throw new Error('Invalid GeoJSON response from the server.');
            }

            if (facilitiesLayer) {
                map.removeLayer(facilitiesLayer);
                facilitiesLayer = null;
            }

            const markers = [];

            facilitiesLayer = L.geoJSON(data, {
                pointToLayer: function (feature, latlng) {
                    return L.marker(latlng);
                },

                onEachFeature: function (feature, layer) {
                    const props = feature.properties || {};
                    const geometry = feature.geometry || {};
                    const coords = geometry.coordinates || [];

                    const lon = parseFloat(coords[0]);
                    const lat = parseFloat(coords[1]);

                    let distanceText = '';

                    if (
                        userCoords &&
                        Number.isFinite(lat) &&
                        Number.isFinite(lon)
                    ) {
                        const distance = getDistanceKm(
                            userCoords[0],
                            userCoords[1],
                            lat,
                            lon
                        );

                        distanceText = `
                            <div class="map-popup-distance">
                                <i class="fa-solid fa-location-arrow"></i>
                                ${distance.toFixed(2)} km away
                            </div>
                        `;
                    }

                    let statusColor = '#10b981';

                    if (props.status === 'Busy') {
                        statusColor = '#f59e0b';
                    } else if (props.status === 'Emergency Only') {
                        statusColor = '#ef4444';
                    }

                    const name = props.name || 'Healthcare Facility';
                    const type = props.type || 'Healthcare Facility';
                    const status = props.status || 'Unknown';
                    const address = props.address || 'Address unavailable';
                    const phone = props.phone || 'Phone unavailable';
                    const detailUrl = props.detail_url || '#';

                    const popupHtml = `
                        <div style="min-width:220px;">
                            <h4 class="map-popup-title">
                                ${escapeHtml(name)}
                            </h4>

                            <span class="map-popup-type">
                                ${escapeHtml(type)}
                            </span>

                            <span
                                class="map-popup-status"
                                style="color:${statusColor};"
                            >
                                ● ${escapeHtml(status)}
                            </span>

                            <p class="map-popup-address">
                                <i class="fa-solid fa-location-dot"></i>
                                ${escapeHtml(address)}
                            </p>

                            <p class="map-popup-phone">
                                <i class="fa-solid fa-phone"></i>
                                ${escapeHtml(phone)}
                            </p>

                            ${distanceText}

                            <a
                                href="${escapeAttribute(detailUrl)}"
                                class="map-popup-link"
                            >
                                View Full Details
                            </a>
                        </div>
                    `;

                    layer.bindPopup(popupHtml);
                    markers.push(layer);
                }
            }).addTo(map);

            if (markers.length > 0) {
                const group = L.featureGroup(markers);

                if (userLocationMarker) {
                    group.addLayer(userLocationMarker);
                }

                const bounds = group.getBounds();

                if (bounds.isValid()) {
                    map.fitBounds(bounds.pad(0.15));
                }
            } else if (userCoords) {
                map.setView(userCoords, 13);
            } else {
                map.setView([defaultLat, defaultLon], 12);
            }

            hideLoading();

            setTimeout(function () {
                map.invalidateSize();
            }, 200);

        } catch (error) {
            console.error('Error loading facilities GeoJSON:', error);

            showError(
                'Unable to load healthcare facilities. Please check your API endpoint.'
            );
        }
    }

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function (position) {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;

                if (
                    !Number.isFinite(lat) ||
                    !Number.isFinite(lon)
                ) {
                    fetchAndPlotMarkers();
                    return;
                }

                userCoords = [lat, lon];

                if (userLocationMarker) {
                    map.removeLayer(userLocationMarker);
                }

                userLocationMarker = L.marker(
                    [lat, lon],
                    {
                        icon: userIcon,
                        zIndexOffset: 1000
                    }
                ).addTo(map);

                userLocationMarker
                    .bindPopup('<strong>Your Current Location</strong>');

                fetchAndPlotMarkers();
            },
            function () {
                fetchAndPlotMarkers();
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 60000
            }
        );
    } else {
        fetchAndPlotMarkers();
    }

    window.addEventListener('resize', function () {
        setTimeout(function () {
            map.invalidateSize();
        }, 100);
    });

    setTimeout(function () {
        map.invalidateSize();
    }, 300);

    function getDistanceKm(lat1, lon1, lat2, lon2) {
        const radius = 6371;

        const dLat = toRadians(lat2 - lat1);
        const dLon = toRadians(lon2 - lon1);

        const a =
            Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(toRadians(lat1)) *
                Math.cos(toRadians(lat2)) *
                Math.sin(dLon / 2) *
                Math.sin(dLon / 2);

        const c =
            2 * Math.atan2(
                Math.sqrt(a),
                Math.sqrt(1 - a)
            );

        return radius * c;
    }

    function toRadians(degrees) {
        return degrees * (Math.PI / 180);
    }

    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function escapeAttribute(value) {
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }
});