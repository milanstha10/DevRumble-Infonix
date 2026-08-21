from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class HealthcareFacility(models.Model):

    # =========================================================
    # CHOICES
    # =========================================================

    TYPE_CHOICES = [
        ("Hospital", "Hospital"),
        ("Clinic", "Clinic"),
        ("Health Post", "Health Post"),
        ("Pharmacy", "Pharmacy"),
    ]

    STATUS_CHOICES = [
        ("Available", "Available"),
        ("Busy", "Busy"),
        ("Emergency Only", "Emergency Only"),
    ]

    # =========================================================
    # BASIC INFORMATION
    # =========================================================

    name = models.CharField(
        max_length=255,
        db_index=True,
    )

    type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        db_index=True,
    )

    address = models.CharField(
        max_length=255,
    )

    phone = models.CharField(
        max_length=50,
        blank=True,
        default="",
    )

    website = models.URLField(
        max_length=500,
        blank=True,
        default="",
    )

    # =========================================================
    # SPECIALIZATIONS
    # =========================================================

    specializations_raw = models.TextField(
        blank=True,
        default="",
        help_text=(
            "Comma-separated specializations or doctor services."
        ),
    )

    # =========================================================
    # MAP COORDINATES
    # =========================================================

    latitude = models.FloatField(
        validators=[
            MinValueValidator(-90.0),
            MaxValueValidator(90.0),
        ],
        help_text="Latitude between -90 and 90.",
    )

    longitude = models.FloatField(
        validators=[
            MinValueValidator(-180.0),
            MaxValueValidator(180.0),
        ],
        help_text="Longitude between -180 and 180.",
    )

    # =========================================================
    # FACILITY STATUS
    # =========================================================

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="Available",
        db_index=True,
    )

    # =========================================================
    # TIMESTAMPS
    # =========================================================

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    # =========================================================
    # PROPERTIES
    # =========================================================

    @property
    def specializations_list(self):
        """
        Return specializations as a clean Python list.

        Example:

            "Cardiology,Neurology,Pediatrics"

        becomes:

            [
                "Cardiology",
                "Neurology",
                "Pediatrics"
            ]
        """

        if not self.specializations_raw:
            return []

        specializations = []

        seen = set()

        for item in self.specializations_raw.split(","):

            value = item.strip()

            if not value:
                continue

            normalized = value.casefold()

            if normalized in seen:
                continue

            seen.add(normalized)
            specializations.append(value)

        return specializations

    @property
    def coordinates(self):
        """
        Return coordinates in Leaflet-friendly format.

        Leaflet expects:

            [latitude, longitude]
        """

        return [
            self.latitude,
            self.longitude,
        ]

    @property
    def geojson_coordinates(self):
        """
        Return coordinates in GeoJSON format.

        GeoJSON expects:

            [longitude, latitude]
        """

        return [
            self.longitude,
            self.latitude,
        ]

    # =========================================================
    # STRING REPRESENTATION
    # =========================================================

    def __str__(self):
        return f"{self.name} ({self.type})"

    # =========================================================
    # META
    # =========================================================

    class Meta:
        ordering = ["name"]

        indexes = [
            models.Index(
                fields=["type"],
                name="facility_type_idx",
            ),
            models.Index(
                fields=["status"],
                name="facility_status_idx",
            ),
            models.Index(
                fields=["name"],
                name="facility_name_idx",
            ),
        ]