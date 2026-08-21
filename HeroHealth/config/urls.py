from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("health.urls")),
    path("accounts/", include("accounts.urls")),
    path("facilities/", include("facilities.urls")),
]