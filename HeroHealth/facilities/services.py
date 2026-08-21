import json
import os

from django.conf import settings

from .models import HealthcareFacility


# =========================================================
# TEXT CLEANING
# =========================================================

def _clean_text(value, default=""):
    """
    Convert a value into a clean string.

    None and empty values are converted to the supplied default.
    """

    if value is None:
        return default

    return str(value).strip()


# =========================================================
# SPECIALIZATION CLEANING
# =========================================================

def _clean_specializations(value):
    """
    Convert JSON specialization data into a clean,
    comma-separated string.

    Supported input:

        [
            "Cardiology",
            "Neurology",
            "Emergency Medicine"
        ]

    or:

        "Cardiology, Neurology"

    Returns:

        "Cardiology,Neurology,Emergency Medicine"
    """

    if not value:
        return ""

    if isinstance(value, str):

        items = value.split(",")

    elif isinstance(value, list):

        items = value

    else:

        return ""

    cleaned = []

    existing_lower = set()

    for item in items:

        specialization = _clean_text(item)

        if not specialization:
            continue

        normalized = specialization.casefold()

        if normalized in existing_lower:
            continue

        cleaned.append(
            specialization
        )

        existing_lower.add(
            normalized
        )

    return ",".join(cleaned)


# =========================================================
# COORDINATE CLEANING
# =========================================================

def _clean_coordinate(
    value,
    minimum,
    maximum,
):
    """
    Validate and normalize a geographic coordinate.

    Returns:
        float if valid
        None if invalid
    """

    try:

        coordinate = float(value)

    except (
        TypeError,
        ValueError,
    ):

        return None

    if not (
        minimum <= coordinate <= maximum
    ):

        return None

    return coordinate


# =========================================================
# COORDINATE SANITY CHECK
# =========================================================

def _coordinates_look_valid(
    latitude,
    longitude,
):
    """
    Perform additional sanity checks on coordinates.

    This does not attempt to geocode addresses. It only prevents
    obviously broken coordinate data from entering the database.
    """

    if latitude is None or longitude is None:
        return False

    if not (
        -90 <= latitude <= 90
    ):
        return False

    if not (
        -180 <= longitude <= 180
    ):
        return False

    # 0,0 is almost always accidental for a Nepal facility.
    #
    # We don't reject every possible global 0,0 coordinate in
    # a generic application, but HeroHealth is specifically
    # dealing with Nepal healthcare facilities.
    if (
        latitude == 0
        and longitude == 0
    ):
        return False

    return True


# =========================================================
# LOAD FACILITIES
# =========================================================

def load_facilities_from_json():
    """
    Load healthcare facilities from:

        BASE_DIR/data/facilities.json

    The importer is defensive so that malformed records do not
    prevent valid facilities from being imported.

    Existing facilities are not overwritten.

    Returns:
        int: number of newly created facilities.
    """

    json_path = os.path.join(
        settings.BASE_DIR,
        "data",
        "facilities.json",
    )

    # =====================================================
    # CHECK FILE
    # =====================================================

    if not os.path.exists(
        json_path
    ):

        print(
            "JSON data file not found at: "
            f"{json_path}"
        )

        return 0

    # =====================================================
    # READ JSON
    # =====================================================

    try:

        with open(
            json_path,
            "r",
            encoding="utf-8",
        ) as file:

            facilities_data = json.load(
                file
            )

    except json.JSONDecodeError as error:

        print(
            "Failed to parse facilities JSON: "
            f"{error}"
        )

        return 0

    except OSError as error:

        print(
            "Failed to read facilities JSON: "
            f"{error}"
        )

        return 0

    # =====================================================
    # VALIDATE TOP LEVEL
    # =====================================================

    if not isinstance(
        facilities_data,
        list,
    ):

        print(
            "Invalid facilities JSON format. "
            "Expected a list of facility objects."
        )

        return 0

    # =====================================================
    # VALID CHOICES
    # =====================================================

    valid_types = {
        choice[0]
        for choice in HealthcareFacility.TYPE_CHOICES
    }

    valid_statuses = {
        choice[0]
        for choice in HealthcareFacility.STATUS_CHOICES
    }

    # =====================================================
    # COUNTERS
    # =====================================================

    created_count = 0
    skipped_count = 0
    duplicate_count = 0

    # =====================================================
    # PROCESS RECORDS
    # =====================================================

    for index, item in enumerate(
        facilities_data,
        start=1,
    ):

        # -------------------------------------------------
        # RECORD TYPE
        # -------------------------------------------------

        if not isinstance(
            item,
            dict,
        ):

            print(
                f"Skipping facility #{index}: "
                "expected an object."
            )

            skipped_count += 1
            continue

        # -------------------------------------------------
        # BASIC INFORMATION
        # -------------------------------------------------

        name = _clean_text(
            item.get("name")
        )

        facility_type = _clean_text(
            item.get("type")
        )

        address = _clean_text(
            item.get("address")
        )

        phone = _clean_text(
            item.get("phone")
        )

        website = _clean_text(
            item.get("website")
        )

        # -------------------------------------------------
        # NAME
        # -------------------------------------------------

        if not name:

            print(
                f"Skipping facility #{index}: "
                "missing name."
            )

            skipped_count += 1
            continue

        # -------------------------------------------------
        # FACILITY TYPE
        # -------------------------------------------------

        if not facility_type:

            print(
                f"Skipping '{name}': "
                "missing facility type."
            )

            skipped_count += 1
            continue

        if facility_type not in valid_types:

            print(
                f"Skipping '{name}': "
                f"invalid facility type "
                f"'{facility_type}'. "
                f"Expected one of: "
                f"{sorted(valid_types)}"
            )

            skipped_count += 1
            continue

        # -------------------------------------------------
        # ADDRESS
        # -------------------------------------------------

        if not address:

            address = "Address unavailable"

        # -------------------------------------------------
        # COORDINATES
        # -------------------------------------------------

        latitude = _clean_coordinate(
            item.get("latitude"),
            -90.0,
            90.0,
        )

        longitude = _clean_coordinate(
            item.get("longitude"),
            -180.0,
            180.0,
        )

        if latitude is None:

            print(
                f"Skipping '{name}': "
                f"invalid latitude "
                f"({item.get('latitude')!r})."
            )

            skipped_count += 1
            continue

        if longitude is None:

            print(
                f"Skipping '{name}': "
                f"invalid longitude "
                f"({item.get('longitude')!r})."
            )

            skipped_count += 1
            continue

        if not _coordinates_look_valid(
            latitude,
            longitude,
        ):

            print(
                f"Skipping '{name}': "
                f"invalid coordinate pair "
                f"({latitude}, {longitude})."
            )

            skipped_count += 1
            continue

        # -------------------------------------------------
        # SPECIALIZATIONS
        # -------------------------------------------------

        specializations_str = (
            _clean_specializations(
                item.get(
                    "specializations",
                    [],
                )
            )
        )

        # -------------------------------------------------
        # STATUS
        # -------------------------------------------------

        status = _clean_text(
            item.get(
                "status",
                "Available",
            ),
            default="Available",
        )

        if status not in valid_statuses:

            print(
                f"Invalid status '{status}' "
                f"for '{name}'. "
                "Using 'Available'."
            )

            status = "Available"

        # =================================================
        # DUPLICATE CHECK
        # =================================================

        existing = (
            HealthcareFacility.objects
            .filter(
                name__iexact=name
            )
            .first()
        )

        if existing:

            duplicate_count += 1

            continue

        # =================================================
        # CREATE FACILITY
        # =================================================

        try:

            HealthcareFacility.objects.create(

                name=name,

                type=facility_type,

                address=address,

                phone=phone,

                website=website,

                specializations_raw=(
                    specializations_str
                ),

                latitude=latitude,

                longitude=longitude,

                status=status,
            )

            created_count += 1

        except Exception as error:

            print(
                f"Failed to create facility "
                f"'{name}': {error}"
            )

            skipped_count += 1

    # =====================================================
    # IMPORT SUMMARY
    # =====================================================

    print(
        "=========================================="
    )

    print(
        "Healthcare facility import completed."
    )

    print(
        f"Added:      {created_count}"
    )

    print(
        f"Duplicates: {duplicate_count}"
    )

    print(
        f"Skipped:    {skipped_count}"
    )

    print(
        "=========================================="
    )

    return created_count