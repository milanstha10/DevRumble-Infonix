/* =========================================================
   HEROHEALTH — MAP.JS
   Supports:
   1. Facility search/proximity map
   2. Facility detail map
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {

    /*
     * Leaflet must be loaded before this script.
     */
    if (typeof L === 'undefined') {
        console.error('HeroHealth: Leaflet is not loaded.');
        return;
    }


    /* =====================================================
       SHARED HELPERS
       ===================================================== */

    function escapeHtml(value) {

        if (
            value === null ||
            value === undefined
        ) {
            return '';
        }

        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }


    function getFacilityColor(properties) {

        const status = String(
            properties?.status || ''
        ).toLowerCase();

        if (status.includes('emergency')) {
            return '#ef4444';
        }

        if (status.includes('busy')) {
            return '#f59e0b';
        }

        return '#00f2fe';
    }


    function createFacilityIcon(color) {

        return L.divIcon({
            className: 'facility-marker',

            html:
                '<div class="facility-marker-inner" ' +
                'style="background:' +
                escapeHtml(color) +
                ';"></div>',

            iconSize: [18, 18],
            iconAnchor: [9, 9],
            popupAnchor: [0, -9]
        });
    }


    function getDistanceKm(
        lat1,
        lon1,
        lat2,
        lon2
    ) {

        const earthRadius = 6371;

        const latitudeDifference =
            toRadians(lat2 - lat1);

        const longitudeDifference =
            toRadians(lon2 - lon1);

        const a =
            Math.sin(
                latitudeDifference / 2
            ) ** 2 +

            Math.cos(
                toRadians(lat1)
            ) *

            Math.cos(
                toRadians(lat2)
            ) *

            Math.sin(
                longitudeDifference / 2
            ) ** 2;

        const c =
            2 *
            Math.atan2(
                Math.sqrt(a),
                Math.sqrt(1 - a)
            );

        return earthRadius * c;
    }


    function toRadians(value) {

        return value *
            Math.PI /
            180;
    }


    /* =====================================================
       OPENSTREETMAP TILE LAYER
       ===================================================== */

    function addBaseTiles(map) {

        L.tileLayer(
            'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
            {
                minZoom: 3,
                maxZoom: 19,

                attribution:
                    '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">' +
                    'OpenStreetMap</a> contributors'
            }
        ).addTo(map);
    }


    /* =====================================================
       MAP SIZE FIX
       ===================================================== */

    function invalidateMapSize(map) {

        setTimeout(function () {

            if (map) {
                map.invalidateSize(true);
            }

        }, 100);


        setTimeout(function () {

            if (map) {
                map.invalidateSize(true);
            }

        }, 500);


        setTimeout(function () {

            if (map) {
                map.invalidateSize(true);
            }

        }, 1000);
    }


    /* =====================================================
       FACILITY DETAIL MAP
       ===================================================== */

    function initializeFacilityDetailMap() {

        const mapElement =
            document.getElementById(
                'facilityDetailMap'
            );

        if (!mapElement) {
            return;
        }


        console.log(
            'HeroHealth: Initializing facility detail map.'
        );


        /* -------------------------------------------------
           READ DATA FROM HTML
           ------------------------------------------------- */

        const latitude =
            Number(
                mapElement.dataset.lat
            );

        const longitude =
            Number(
                mapElement.dataset.lon
            );

        const name =
            mapElement.dataset.name ||
            'Healthcare Facility';

        const address =
            mapElement.dataset.address ||
            'Address unavailable';


        /* -------------------------------------------------
           VALIDATE COORDINATES
           ------------------------------------------------- */

        if (
            !Number.isFinite(latitude) ||
            !Number.isFinite(longitude) ||
            latitude < -90 ||
            latitude > 90 ||
            longitude < -180 ||
            longitude > 180
        ) {

            console.error(
                'HeroHealth: Invalid facility coordinates.',
                {
                    latitude: latitude,
                    longitude: longitude
                }
            );

            mapElement.innerHTML = `
                <div class="map-error">
                    Unable to display this facility location.
                    Invalid coordinates were provided.
                </div>
            `;

            return;
        }


        /* -------------------------------------------------
           CREATE MAP
           ------------------------------------------------- */

        const map =
            L.map(
                mapElement,
                {
                    center: [
                        latitude,
                        longitude
                    ],

                    zoom: 15,

                    zoomControl: true,

                    scrollWheelZoom: true,

                    dragging: true,

                    touchZoom: true,

                    doubleClickZoom: true,

                    boxZoom: true,

                    keyboard: true,

                    attributionControl: true
                }
            );


        /* -------------------------------------------------
           TILE LAYER
           ------------------------------------------------- */

        addBaseTiles(map);


        /* -------------------------------------------------
           FACILITY MARKER
           ------------------------------------------------- */

        const marker =
            L.marker(
                [
                    latitude,
                    longitude
                ],
                {
                    icon:
                        createFacilityIcon(
                            '#00f2fe'
                        )
                }
            )
            .addTo(map);


        /* -------------------------------------------------
           POPUP
           ------------------------------------------------- */

        const safeName =
            escapeHtml(name);

        const safeAddress =
            escapeHtml(address);


        marker.bindPopup(`
            <div class="facility-popup">

                <h4 class="facility-popup-title">
                    ${safeName}
                </h4>

                <p class="facility-popup-address">
                    <i class="fa-solid fa-location-dot"></i>
                    ${safeAddress}
                </p>

                <p class="facility-popup-coordinates">
                    <strong>Latitude:</strong>
                    ${latitude.toFixed(6)}
                    <br>

                    <strong>Longitude:</strong>
                    ${longitude.toFixed(6)}
                </p>

            </div>
        `);


        /* -------------------------------------------------
           OPEN POPUP
           ------------------------------------------------- */

        marker.openPopup();


        /* -------------------------------------------------
           FORCE LEAFLET TO RECALCULATE SIZE
           ------------------------------------------------- */

        invalidateMapSize(map);


        /* -------------------------------------------------
           WINDOW RESIZE
           ------------------------------------------------- */

        window.addEventListener(
            'resize',
            function () {

                map.invalidateSize(true);

            }
        );


        /* -------------------------------------------------
           STORE MAP INSTANCE
           ------------------------------------------------- */

        mapElement._heroHealthMap = map;


        console.log(
            'HeroHealth: Facility detail map initialized.',
            {
                latitude: latitude,
                longitude: longitude
            }
        );
    }


    /* =====================================================
       SEARCH / PROXIMITY MAP
       ===================================================== */

    function initializeSearchMap() {

        const mapElement =
            document.getElementById(
                'searchMap'
            );

        if (!mapElement) {
            return;
        }


        console.log(
            'HeroHealth: Initializing facility search map.'
        );


        const loadingElement =
            document.getElementById(
                'mapLoading'
            );

        const errorElement =
            document.getElementById(
                'mapError'
            );

        const locateButton =
            document.getElementById(
                'locateMeButton'
            );

        const resultStatus =
            document.getElementById(
                'mapResultStatus'
            );


        /* -------------------------------------------------
           SPECIALTY
           ------------------------------------------------- */

        const specialty =
            mapElement.dataset.specialty ||
            '';


        /* -------------------------------------------------
           DEFAULT LOCATION — KATHMANDU
           ------------------------------------------------- */

        const defaultLocation = {
            lat: 27.7172,
            lon: 85.3240,
            zoom: 12
        };


        /* -------------------------------------------------
           STATE
           ------------------------------------------------- */

        let map = null;

        let userLocationMarker = null;

        let userAccuracyCircle = null;

        let userCoords = null;

        let facilitiesLayer = null;

        let locationRequested = false;

        let facilitiesLoaded = false;


        /* -------------------------------------------------
           LOADING
           ------------------------------------------------- */

        function setLoading(isLoading) {

            if (!loadingElement) {
                return;
            }

            loadingElement.classList.toggle(
                'hidden',
                !isLoading
            );
        }


        /* -------------------------------------------------
           ERROR
           ------------------------------------------------- */

        function showError(message) {

            if (!errorElement) {

                console.error(message);

                return;
            }

            errorElement.textContent =
                message;

            errorElement.hidden = false;
        }


        function hideError() {

            if (!errorElement) {
                return;
            }

            errorElement.textContent = '';

            errorElement.hidden = true;
        }


        /* -------------------------------------------------
           RESULT STATUS
           ------------------------------------------------- */

        function updateResultStatus(message) {

            if (!resultStatus) {
                return;
            }

            resultStatus.textContent =
                message || '';
        }


        /* -------------------------------------------------
           LOCATE BUTTON
           ------------------------------------------------- */

        function setLocateButtonLoading(
            isLoading
        ) {

            if (!locateButton) {
                return;
            }

            locateButton.classList.toggle(
                'loading',
                isLoading
            );

            locateButton.innerHTML =
                isLoading

                    ? '<i class="fa-solid fa-spinner fa-spin"></i>'

                    : '<i class="fa-solid fa-location-crosshairs"></i>';
        }


        /* -------------------------------------------------
           CREATE SEARCH MAP
           ------------------------------------------------- */

        function createSearchMap() {

            map =
                L.map(
                    'searchMap',
                    {
                        center: [
                            defaultLocation.lat,
                            defaultLocation.lon
                        ],

                        zoom:
                            defaultLocation.zoom,

                        zoomControl: true,

                        scrollWheelZoom: true,

                        dragging: true,

                        touchZoom: true,

                        doubleClickZoom: true,

                        boxZoom: true,

                        keyboard: true,

                        attributionControl: true
                    }
                );


            addBaseTiles(map);


            invalidateMapSize(map);


            window.addEventListener(
                'resize',
                function () {

                    if (map) {
                        map.invalidateSize(true);
                    }

                }
            );
        }


        /* -------------------------------------------------
           USER ICON
           ------------------------------------------------- */

        function createUserIcon() {

            return L.divIcon({
                className:
                    'user-location-pulsing-icon',

                html:
                    '<div class="user-location-marker"></div>',

                iconSize: [22, 22],

                iconAnchor: [11, 11],

                popupAnchor: [0, -12]
            });
        }


        /* -------------------------------------------------
           UPDATE USER LOCATION
           ------------------------------------------------- */

        function updateUserLocation(
            lat,
            lon,
            accuracy
        ) {

            if (
                !Number.isFinite(lat) ||
                !Number.isFinite(lon)
            ) {
                return;
            }


            userCoords = {
                lat: lat,
                lon: lon,

                accuracy:
                    Number.isFinite(accuracy)
                        ? accuracy
                        : null
            };


            /* Remove previous marker */

            if (userLocationMarker) {

                map.removeLayer(
                    userLocationMarker
                );
            }


            /* Remove previous accuracy circle */

            if (userAccuracyCircle) {

                map.removeLayer(
                    userAccuracyCircle
                );
            }


            /* Create user marker */

            userLocationMarker =
                L.marker(
                    [
                        lat,
                        lon
                    ],
                    {
                        icon:
                            createUserIcon(),

                        zIndexOffset: 1000
                    }
                )
                .addTo(map);


            let accuracyText = '';


            if (
                Number.isFinite(accuracy) &&
                accuracy > 0
            ) {

                accuracyText =
                    '<br>Accuracy: ' +
                    (
                        accuracy >= 1000

                            ? (
                                accuracy / 1000
                            ).toFixed(2) +
                            ' km'

                            : Math.round(
                                accuracy
                            ) +
                            ' m'
                    );
            }


            userLocationMarker.bindPopup(
                '<strong>Your Current Location</strong>' +

                '<br>Latitude: ' +
                lat.toFixed(6) +

                '<br>Longitude: ' +
                lon.toFixed(6) +

                accuracyText
            );


            /* Accuracy circle */

            if (
                Number.isFinite(accuracy) &&
                accuracy > 0 &&
                accuracy <= 10000
            ) {

                userAccuracyCircle =
                    L.circle(
                        [
                            lat,
                            lon
                        ],
                        {
                            radius: accuracy,

                            color: '#00ff87',

                            fillColor: '#00ff87',

                            fillOpacity: 0.08,

                            weight: 1,

                            className:
                                'user-accuracy-circle'
                        }
                    )
                    .addTo(map);
            }


            /* Center on user */

            map.setView(
                [
                    lat,
                    lon
                ],
                15,
                {
                    animate: true
                }
            );


            /* Refresh facility distances */

            if (facilitiesLoaded) {

                refreshFacilityPopups();
            }
        }


        /* -------------------------------------------------
           REQUEST USER LOCATION
           ------------------------------------------------- */

        function requestLocation() {

            if (locationRequested) {
                return;
            }

            locationRequested = true;


            if (!navigator.geolocation) {

                showError(
                    'Geolocation is not supported by this browser. Showing Kathmandu instead.'
                );

                return;
            }


            hideError();

            setLocateButtonLoading(true);


            navigator.geolocation.getCurrentPosition(

                function (position) {

                    const latitude =
                        Number(
                            position.coords.latitude
                        );

                    const longitude =
                        Number(
                            position.coords.longitude
                        );

                    const accuracy =
                        Number(
                            position.coords.accuracy
                        );


                    updateUserLocation(
                        latitude,
                        longitude,
                        accuracy
                    );


                    setLocateButtonLoading(
                        false
                    );
                },


                function (error) {

                    setLocateButtonLoading(
                        false
                    );


                    let message =
                        'Unable to access your location. Showing Kathmandu instead.';


                    if (
                        error.code ===
                        error.PERMISSION_DENIED
                    ) {

                        message =
                            'Location permission was denied. You can enable it and press the location button again.';
                    }


                    if (
                        error.code ===
                        error.POSITION_UNAVAILABLE
                    ) {

                        message =
                            'Your location is currently unavailable. Showing Kathmandu instead.';
                    }


                    if (
                        error.code ===
                        error.TIMEOUT
                    ) {

                        message =
                            'Location request timed out. Showing Kathmandu instead.';
                    }


                    showError(message);
                },


                {
                    enableHighAccuracy: true,

                    timeout: 20000,

                    maximumAge: 0
                }
            );
        }


        /* -------------------------------------------------
           REQUEST LOCATION AGAIN
           ------------------------------------------------- */

        function requestLocationAgain() {

            locationRequested = false;

            requestLocation();
        }


        /* -------------------------------------------------
           BUILD FACILITY POPUP
           ------------------------------------------------- */

        function buildFacilityPopup(
            properties,
            facilityLat,
            facilityLon
        ) {

            const name =
                escapeHtml(
                    properties.name ||
                    'Healthcare Facility'
                );


            const type =
                escapeHtml(
                    properties.type ||
                    'Healthcare Facility'
                );


            const status =
                escapeHtml(
                    properties.status ||
                    'Available'
                );


            const address =
                escapeHtml(
                    properties.address ||
                    'Address unavailable'
                );


            const phone =
                escapeHtml(
                    properties.phone ||
                    'Not available'
                );


            const detailUrl =
                escapeHtml(
                    properties.detail_url ||
                    '#'
                );


            let distanceHtml = '';


            if (userCoords) {

                const distance =
                    getDistanceKm(
                        userCoords.lat,
                        userCoords.lon,
                        facilityLat,
                        facilityLon
                    );


                distanceHtml =
                    '<div class="facility-popup-distance">' +

                    '<i class="fa-solid fa-route"></i> ' +

                    distance.toFixed(2) +

                    ' km away' +

                    '</div>';
            }


            const statusColor =
                getFacilityColor(
                    properties
                );


            return `
                <div class="facility-popup">

                    <h4 class="facility-popup-title">
                        ${name}
                    </h4>

                    <span class="facility-popup-type">
                        ${type}
                    </span>

                    <span
                        class="facility-popup-status"
                        style="color:${statusColor};"
                    >
                        ● ${status}
                    </span>

                    <p class="facility-popup-address">
                        <i class="fa-solid fa-location-dot"></i>
                        ${address}
                    </p>

                    <p class="facility-popup-phone">
                        <i class="fa-solid fa-phone"></i>
                        ${phone}
                    </p>

                    ${distanceHtml}

                    <a
                        href="${detailUrl}"
                        class="facility-popup-link"
                    >
                        View Full Details
                    </a>

                </div>
            `;
        }


        /* -------------------------------------------------
           FETCH FACILITIES
           ------------------------------------------------- */

        function fetchAndPlotFacilities() {

            if (!map) {
                return;
            }


            setLoading(true);

            hideError();


            let apiUrl =
                mapElement.dataset.apiUrl ||
                '/facilities/api/geojson/';


            if (specialty) {

                apiUrl +=
                    '?specialty=' +
                    encodeURIComponent(
                        specialty
                    );
            }


            fetch(
                apiUrl,
                {
                    method: 'GET',

                    headers: {
                        Accept:
                            'application/json'
                    },

                    credentials:
                        'same-origin',

                    cache:
                        'no-store'
                }
            )

                .then(function (response) {

                    if (!response.ok) {

                        throw new Error(
                            'API returned HTTP ' +
                            response.status
                        );
                    }

                    return response.json();
                })


                .then(function (data) {

                    if (
                        !data ||
                        data.type !==
                            'FeatureCollection' ||
                        !Array.isArray(
                            data.features
                        )
                    ) {

                        throw new Error(
                            'Invalid GeoJSON response.'
                        );
                    }


                    if (facilitiesLayer) {

                        map.removeLayer(
                            facilitiesLayer
                        );

                        facilitiesLayer = null;
                    }


                    const validFeatures =
                        data.features.filter(
                            function (feature) {

                                if (
                                    !feature ||
                                    !feature.geometry ||
                                    feature.geometry.type !==
                                        'Point' ||
                                    !Array.isArray(
                                        feature.geometry.coordinates
                                    )
                                ) {

                                    return false;
                                }


                                const lon =
                                    Number(
                                        feature.geometry.coordinates[0]
                                    );


                                const lat =
                                    Number(
                                        feature.geometry.coordinates[1]
                                    );


                                return (
                                    Number.isFinite(lat) &&
                                    Number.isFinite(lon) &&
                                    lat >= -90 &&
                                    lat <= 90 &&
                                    lon >= -180 &&
                                    lon <= 180
                                );
                            }
                        );


                    if (
                        validFeatures.length === 0
                    ) {

                        facilitiesLayer =
                            L.layerGroup()
                                .addTo(map);


                        setLoading(false);


                        updateResultStatus(
                            'No healthcare facilities found.'
                        );


                        showError(
                            'No healthcare facilities with valid map coordinates were found.'
                        );


                        map.setView(
                            [
                                defaultLocation.lat,
                                defaultLocation.lon
                            ],
                            defaultLocation.zoom
                        );


                        return;
                    }


                    facilitiesLayer =
                        L.geoJSON(
                            {
                                type:
                                    'FeatureCollection',

                                features:
                                    validFeatures
                            },
                            {

                                pointToLayer:
                                    function (
                                        feature,
                                        latlng
                                    ) {

                                        const color =
                                            getFacilityColor(
                                                feature.properties
                                            );


                                        return L.marker(
                                            latlng,
                                            {
                                                icon:
                                                    createFacilityIcon(
                                                        color
                                                    )
                                            }
                                        );
                                    },


                                onEachFeature:
                                    function (
                                        feature,
                                        layer
                                    ) {

                                        layer.bindPopup(
                                            buildFacilityPopup(
                                                feature.properties ||
                                                    {},

                                                Number(
                                                    feature.geometry.coordinates[1]
                                                ),

                                                Number(
                                                    feature.geometry.coordinates[0]
                                                )
                                            )
                                        );
                                    }
                            }
                        )
                        .addTo(map);


                    facilitiesLoaded = true;


                    updateResultStatus(
                        validFeatures.length +
                        (
                            validFeatures.length === 1
                                ? ' healthcare facility found.'
                                : ' healthcare facilities found.'
                        )
                    );


                    fitMapToFacilities(
                        validFeatures
                    );


                    setLoading(false);
                })


                .catch(function (error) {

                    console.error(
                        'Healthcare facility API error:',
                        error
                    );


                    facilitiesLoaded = false;


                    setLoading(false);


                    updateResultStatus(
                        ''
                    );


                    showError(
                        'Unable to load healthcare facilities. Please check that the GeoJSON API is available.'
                    );
                });
        }


        /* -------------------------------------------------
           REFRESH POPUPS
           ------------------------------------------------- */

        function refreshFacilityPopups() {

            if (!facilitiesLayer) {
                return;
            }


            facilitiesLayer.eachLayer(
                function (layer) {

                    const feature =
                        layer.feature;


                    if (
                        !feature ||
                        !feature.geometry ||
                        !feature.geometry.coordinates
                    ) {
                        return;
                    }


                    const properties =
                        feature.properties ||
                        {};


                    const lat =
                        Number(
                            feature.geometry.coordinates[1]
                        );


                    const lon =
                        Number(
                            feature.geometry.coordinates[0]
                        );


                    layer.setPopupContent(
                        buildFacilityPopup(
                            properties,
                            lat,
                            lon
                        )
                    );
                }
            );
        }


        /* -------------------------------------------------
           FIT MAP TO FACILITIES
           ------------------------------------------------- */

        function fitMapToFacilities(
            features
        ) {

            const bounds = [];


            features.forEach(
                function (feature) {

                    const coordinates =
                        feature.geometry.coordinates;


                    const lon =
                        Number(
                            coordinates[0]
                        );


                    const lat =
                        Number(
                            coordinates[1]
                        );


                    bounds.push([
                        lat,
                        lon
                    ]);
                }
            );


            if (userCoords) {

                bounds.push([
                    userCoords.lat,
                    userCoords.lon
                ]);
            }


            if (!bounds.length) {
                return;
            }


            if (bounds.length === 1) {

                map.setView(
                    bounds[0],
                    15
                );

                return;
            }


            const leafletBounds =
                L.latLngBounds(
                    bounds
                );


            map.fitBounds(
                leafletBounds,
                {
                    paddingTopLeft:
                        [40, 40],

                    paddingBottomRight:
                        [40, 40],

                    maxZoom: 15,

                    animate: true
                }
            );
        }


        /* -------------------------------------------------
           LOCATE BUTTON EVENT
           ------------------------------------------------- */

        if (locateButton) {

            locateButton.addEventListener(
                'click',
                function () {

                    requestLocationAgain();
                }
            );
        }


        /* -------------------------------------------------
           INITIALIZE SEARCH MAP
           ------------------------------------------------- */

        createSearchMap();


        /* -------------------------------------------------
           LOAD FACILITIES
           ------------------------------------------------- */

        fetchAndPlotFacilities();


        /* -------------------------------------------------
           REQUEST LOCATION
           ------------------------------------------------- */

        setTimeout(
            function () {

                requestLocation();

            },
            500
        );
    }


    /* =====================================================
       INITIALIZE BOTH MAP TYPES
       ===================================================== */

    initializeSearchMap();

    initializeFacilityDetailMap();

});