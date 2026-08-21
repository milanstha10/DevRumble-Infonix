from django.contrib import admin

from .models import HealthcareFacility


@admin.register(HealthcareFacility)
class HealthcareFacilityAdmin(admin.ModelAdmin):

    # =========================================================
    # LIST DISPLAY
    # =========================================================

    list_display = [
        "name",
        "type",
        "address",
        "status",
        "latitude",
        "longitude",
        "phone",
        "updated_at",
    ]

    # =========================================================
    # SEARCH
    # =========================================================

    search_fields = [
        "name",
        "address",
        "phone",
        "specializations_raw",
    ]

    # =========================================================
    # FILTERS
    # =========================================================

    list_filter = [
        "type",
        "status",
    ]

    # =========================================================
    # EDIT PAGE
    # =========================================================

    fieldsets = (
        (
            "Facility Information",
            {
                "fields": (
                    "name",
                    "type",
                    "status",
                )
            },
        ),
        (
            "Contact Information",
            {
                "fields": (
                    "address",
                    "phone",
                    "website",
                )
            },
        ),
        (
            "Specializations",
            {
                "fields": (
                    "specializations_raw",
                ),
                "description": (
                    "Enter specialties separated by commas. "
                    "Example: Cardiology, Neurology, Pediatrics"
                ),
            },
        ),
        (
            "Map Location",
            {
                "fields": (
                    "latitude",
                    "longitude",
                ),
                "description": (
                    "Enter the exact geographic coordinates "
                    "of this facility. Latitude must be between "
                    "-90 and 90. Longitude must be between "
                    "-180 and 180."
                ),
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": (
                    "collapse",
                ),
            },
        ),
    )

    # =========================================================
    # READ-ONLY FIELDS
    # =========================================================

    readonly_fields = [
        "created_at",
        "updated_at",
    ]

    # =========================================================
    # DEFAULT ORDERING
    # =========================================================

    ordering = [
        "name",
    ]

    # =========================================================
    # PAGINATION
    # =========================================================

    list_per_page = 25