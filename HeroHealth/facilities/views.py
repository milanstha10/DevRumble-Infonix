from math import atan2, cos, radians, sin, sqrt

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .models import HealthcareFacility
from .services import load_facilities_from_json


# =========================================================
# DATA LOADING
# =========================================================

def ensure_data_loaded():
    """
    Automatically load facility data if the database is empty.

    JSON is used as the initial data source.

    Existing database records are not overwritten by the
    importer, allowing facilities to be managed through
    Django Admin.
    """

    if HealthcareFacility.objects.exists():
        return

    try:
        load_facilities_from_json()

    except Exception as exc:
        print(
            "Failed to auto-load facilities JSON:",
            exc
        )


# =========================================================
# SPECIALTY HELPERS
# =========================================================

def get_available_specialties():
    """
    Return a sorted list of unique specialties across all
    healthcare facilities.
    """

    specialties = set()

    facilities = HealthcareFacility.objects.all()

    for facility in facilities:

        for specialty in facility.specializations_list:

            cleaned_specialty = specialty.strip()

            if cleaned_specialty:
                specialties.add(cleaned_specialty)

    return sorted(
        specialties,
        key=str.casefold
    )


def specialty_matches(
    facility,
    selected_specialty
):
    """
    Perform an exact, case-insensitive specialty match.

    Example:

        Cardiology

    matches:

        Cardiology

    but avoids blindly matching unrelated substrings.
    """

    if not selected_specialty:
        return True

    selected = (
        selected_specialty
        .strip()
        .casefold()
    )

    return any(
        specialty.strip().casefold() == selected
        for specialty in facility.specializations_list
    )


# =========================================================
# COORDINATE HELPERS
# =========================================================

def parse_coordinate(
    value,
    minimum,
    maximum
):
    """
    Safely convert a coordinate to float.

    Returns:
        float or None
    """

    if value is None:
        return None

    try:

        coordinate = float(value)

    except (
        TypeError,
        ValueError
    ):

        return None

    if not (
        minimum <= coordinate <= maximum
    ):

        return None

    return coordinate


def get_distance_km(
    latitude_1,
    longitude_1,
    latitude_2,
    longitude_2
):
    """
    Calculate straight-line distance between two
    geographic coordinates using the Haversine formula.

    Returns distance in kilometers.
    """

    earth_radius_km = 6371.0

    lat1 = radians(latitude_1)
    lat2 = radians(latitude_2)

    delta_lat = radians(
        latitude_2 - latitude_1
    )

    delta_lon = radians(
        longitude_2 - longitude_1
    )

    a = (
        sin(delta_lat / 2) ** 2
        +
        cos(lat1)
        *
        cos(lat2)
        *
        sin(delta_lon / 2) ** 2
    )

    # Protect against tiny floating-point errors.
    a = min(
        1.0,
        max(0.0, a)
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return earth_radius_km * c


# =========================================================
# FACILITY LIST
# =========================================================

def facility_list(request):

    ensure_data_loaded()

    query = request.GET.get(
        "q",
        ""
    ).strip()

    fac_type = request.GET.get(
        "type",
        ""
    ).strip()

    specialty = request.GET.get(
        "specialty",
        ""
    ).strip()

    facilities = HealthcareFacility.objects.all()

    # -----------------------------------------------------
    # TEXT SEARCH
    # -----------------------------------------------------

    if query:

        facilities = (
            facilities.filter(
                name__icontains=query
            )
            |
            facilities.filter(
                address__icontains=query
            )
        )

    # -----------------------------------------------------
    # FACILITY TYPE FILTER
    # -----------------------------------------------------

    if fac_type:

        facilities = facilities.filter(
            type=fac_type
        )

    # -----------------------------------------------------
    # SPECIALTY FILTER
    # -----------------------------------------------------

    if specialty:

        facilities = [
            facility
            for facility in facilities
            if specialty_matches(
                facility,
                specialty
            )
        ]

    # -----------------------------------------------------
    # FILTER OPTIONS
    # -----------------------------------------------------

    all_facilities = (
        HealthcareFacility.objects.all()
    )

    types = (
        all_facilities
        .values_list(
            "type",
            flat=True
        )
        .distinct()
        .order_by("type")
    )

    specialties = (
        get_available_specialties()
    )

    # -----------------------------------------------------
    # CONTEXT
    # -----------------------------------------------------

    context = {

        "facilities": facilities,

        "types": types,

        "specialties": specialties,

        "selected_type": fac_type,

        "selected_specialty": specialty,

        "query": query,
    }

    return render(
        request,
        "facilities/facility_list.html",
        context
    )


# =========================================================
# FACILITY DETAIL
# =========================================================

def facility_detail(
    request,
    pk
):

    ensure_data_loaded()

    facility = get_object_or_404(
        HealthcareFacility,
        pk=pk
    )

    return render(
        request,
        "facilities/facility_detail.html",
        {
            "facility": facility
        }
    )


# =========================================================
# MAP VIEW
# =========================================================

def map_view(request):

    ensure_data_loaded()

    specialties = (
        get_available_specialties()
    )

    selected_specialty = (
        request.GET.get(
            "specialty",
            ""
        ).strip()
    )

    # -----------------------------------------------------
    # Normalize specialty to the actual database spelling.
    # -----------------------------------------------------

    valid_specialty_lookup = {
        specialty.casefold(): specialty
        for specialty in specialties
    }

    if selected_specialty:

        normalized_specialty = (
            selected_specialty.casefold()
        )

        if (
            normalized_specialty
            in valid_specialty_lookup
        ):

            selected_specialty = (
                valid_specialty_lookup[
                    normalized_specialty
                ]
            )

        else:

            selected_specialty = ""

    context = {

        "specialties": specialties,

        "selected_specialty": (
            selected_specialty
        ),
    }

    return render(
        request,
        "facilities/map.html",
        context
    )


# =========================================================
# GEOJSON MAP API
# =========================================================

def facility_geojson_api(request):
    """
    Return healthcare facilities as GeoJSON.

    Supported query parameters:

        specialty
            Filter by exact specialty.

        lat
            User latitude.

        lon
            User longitude.

        radius
            Optional maximum distance in kilometers.

    Example:

        /facilities/api/geojson/
            ?specialty=Cardiology
            &lat=27.7172
            &lon=85.3240

    When lat/lon are supplied:

        - Distance is calculated.
        - Facilities are sorted nearest first.
        - distance_km is included in each feature.

    When radius is supplied:

        Only facilities inside that radius are returned.
    """

    ensure_data_loaded()

    # =====================================================
    # QUERY PARAMETERS
    # =====================================================

    specialty = (
        request.GET.get(
            "specialty",
            ""
        ).strip()
    )

    user_latitude = parse_coordinate(
        request.GET.get("lat"),
        -90.0,
        90.0
    )

    user_longitude = parse_coordinate(
        request.GET.get("lon"),
        -180.0,
        180.0
    )

    radius_km = parse_coordinate(
        request.GET.get("radius"),
        0.0,
        10000.0
    )

    # Only use distance calculations when both coordinates
    # are available.

    has_user_location = (
        user_latitude is not None
        and
        user_longitude is not None
    )

    facilities = (
        HealthcareFacility.objects.all()
    )

    # =====================================================
    # SPECIALTY FILTER
    # =====================================================

    if specialty:

        facilities = [
            facility
            for facility in facilities
            if specialty_matches(
                facility,
                specialty
            )
        ]

    # =====================================================
    # BUILD FEATURES
    # =====================================================

    features = []

    for facility in facilities:

        latitude = parse_coordinate(
            facility.latitude,
            -90.0,
            90.0
        )

        longitude = parse_coordinate(
            facility.longitude,
            -180.0,
            180.0
        )

        # -------------------------------------------------
        # Invalid coordinates
        # -------------------------------------------------

        if (
            latitude is None
            or
            longitude is None
        ):

            continue

        # =================================================
        # DISTANCE
        # =================================================

        distance_km = None

        if has_user_location:

            distance_km = get_distance_km(
                user_latitude,
                user_longitude,
                latitude,
                longitude
            )

            # ---------------------------------------------
            # Optional radius filter
            # ---------------------------------------------

            if (
                radius_km is not None
                and
                distance_km > radius_km
            ):

                continue

        # =================================================
        # PROPERTIES
        # =================================================

        properties = {

            "id": facility.id,

            "name": facility.name,

            "type": facility.type,

            "address": facility.address,

            "phone": (
                facility.phone
                or "N/A"
            ),

            "website": (
                facility.website
                or ""
            ),

            "specializations": (
                facility.specializations_list
            ),

            "status": facility.status,

            "latitude": latitude,

            "longitude": longitude,

            "detail_url": reverse(
                "facility_detail",
                args=[
                    facility.id
                ]
            ),
        }

        # -------------------------------------------------
        # Add distance only when user location is known.
        # -------------------------------------------------

        if distance_km is not None:

            properties[
                "distance_km"
            ] = round(
                distance_km,
                2
            )

        # =================================================
        # GEOJSON FEATURE
        # =================================================

        features.append({

            "type": "Feature",

            "properties": properties,

            "geometry": {

                "type": "Point",

                # GeoJSON MUST be:
                #
                # [longitude, latitude]

                "coordinates": [
                    longitude,
                    latitude
                ],
            },
        })

    # =====================================================
    # SORT BY DISTANCE
    # =====================================================

    if has_user_location:

        features.sort(
            key=lambda feature: (
                feature["properties"]
                .get(
                    "distance_km",
                    float("inf")
                )
            )
        )

    else:

        # Without a user location, keep facilities
        # alphabetically ordered.

        features.sort(
            key=lambda feature: (
                feature["properties"]
                .get(
                    "name",
                    ""
                )
                .casefold()
            )
        )

    # =====================================================
    # RESPONSE
    # =====================================================

    response_data = {

        "type": "FeatureCollection",

        "features": features,

        "count": len(features),

        "selected_specialty": specialty,

        "user_location": None,

        "radius_km": radius_km,
    }

    # -----------------------------------------------------
    # Return user location information when supplied.
    # -----------------------------------------------------

    if has_user_location:

        response_data[
            "user_location"
        ] = {

            "latitude": user_latitude,

            "longitude": user_longitude,
        }

    return JsonResponse(
        response_data
    )