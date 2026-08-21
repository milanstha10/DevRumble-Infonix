document.addEventListener('DOMContentLoaded', function () {

    // =========================================================
    // FIND MAP ELEMENT
    // =========================================================

    const mapElement =
        document.getElementById('facilityDetailMap');

    if (!mapElement) {
        return;
    }


    // =========================================================
    // CHECK LEAFLET
    // =========================================================

    if (typeof L === 'undefined') {

        console.error(
            'Leaflet is not loaded. Make sure Leaflet CSS and JS are included before this script.'
        );

        mapElement.innerHTML = `
            <div class="map-error">
                <i class="fa-solid fa-triangle-exclamation"></i>
                <span>
                    Map library failed to load. Please refresh the page.
                </span>
            </div>
        `;

        return;
    }


    // =========================================================
    // READ FACILITY DATA
    // =========================================================

    const latitude =
        Number(mapElement.dataset.lat);

    const longitude =
        Number(mapElement.dataset.lon);

    const name =
        mapElement.dataset.name ||
        'Healthcare Facility';

    const address =
        mapElement.dataset.address ||
        'Address unavailable';


    // =========================================================
    // VALIDATE COORDINATES
    // =========================================================

    if (
        !Number.isFinite(latitude) ||
        !Number.isFinite(longitude) ||
        latitude < -90 ||
        latitude > 90 ||
        longitude < -180 ||
        longitude > 180
    ) {

        console.error(
            'Invalid facility coordinates:',
            {
                latitude: latitude,
                longitude: longitude
            }
        );

        mapElement.innerHTML = `
            <div class="map-error">
                <i class="fa-solid fa-location-dot"></i>

                <span>
                    Invalid facility coordinates.
                </span>
            </div>
        `;

        return;
    }


    // =========================================================
    // INITIALIZE LEAFLET MAP
    // =========================================================

    const map =
        L.map(
            mapElement,
            {
                center: [
                    latitude,
                    longitude
                ],

                zoom: 16,

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


    // =========================================================
    // OPENSTREETMAP TILE LAYER
    // =========================================================

    L.tileLayer(
        'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        {
            minZoom: 3,

            maxZoom: 19,

            attribution:
                '&copy; ' +
                '<a href="https://www.openstreetmap.org/copyright" ' +
                'target="_blank" ' +
                'rel="noopener noreferrer">' +
                'OpenStreetMap' +
                '</a> contributors'
        }
    ).addTo(map);


    // =========================================================
    // FACILITY ICON
    // =========================================================

    const facilityIcon =
        L.divIcon({
            className:
                'facility-detail-marker',

            html: `
                <div class="facility-detail-marker-inner">
                    <i class="fa-solid fa-hospital"></i>
                </div>
            `,

            iconSize: [
                42,
                42
            ],

            iconAnchor: [
                21,
                42
            ],

            popupAnchor: [
                0,
                -42
            ]
        });


    // =========================================================
    // FACILITY MARKER
    // =========================================================

    const marker =
        L.marker(
            [
                latitude,
                longitude
            ],
            {
                icon: facilityIcon,

                title: name,

                alt: name
            }
        ).addTo(map);


    // =========================================================
    // FACILITY POPUP
    // =========================================================

    marker.bindPopup(
        `
        <div class="facility-detail-popup">

            <div class="facility-detail-popup-title">
                ${escapeHtml(name)}
            </div>

            <div class="facility-detail-popup-address">

                <i class="fa-solid fa-location-dot"></i>

                <span>
                    ${escapeHtml(address)}
                </span>

            </div>

        </div>
        `,
        {
            maxWidth: 300
        }
    );


    // =========================================================
    // OPEN POPUP
    // =========================================================

    marker.openPopup();


    // =========================================================
    // FORCE LEAFLET TO RECALCULATE SIZE
    // =========================================================

    function invalidateMapSize() {

        setTimeout(
            function () {

                map.invalidateSize({
                    pan: false
                });

            },
            100
        );

        setTimeout(
            function () {

                map.invalidateSize({
                    pan: false
                });

            },
            500
        );

        setTimeout(
            function () {

                map.invalidateSize({
                    pan: false
                });

            },
            1000
        );
    }

    invalidateMapSize();


    // =========================================================
    // WINDOW RESIZE
    // =========================================================

    window.addEventListener(
        'resize',
        function () {

            map.invalidateSize({
                pan: false
            });

        }
    );


    // =========================================================
    // HTML ESCAPE
    // =========================================================

    function escapeHtml(value) {

        if (
            value === null ||
            value === undefined
        ) {
            return '';
        }

        return String(value)
            .replace(
                /&/g,
                '&amp;'
            )
            .replace(
                /</g,
                '&lt;'
            )
            .replace(
                />/g,
                '&gt;'
            )
            .replace(
                /"/g,
                '&quot;'
            )
            .replace(
                /'/g,
                '&#039;'
            );
    }

});