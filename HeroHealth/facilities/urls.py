from django.urls import path
from . import views

urlpatterns = [
    path('', views.facility_list, name='facility_list'),
    path('<int:pk>/', views.facility_detail, name='facility_detail'),
    path('map/', views.map_view, name='map_view'),
    path('api/geojson/', views.facility_geojson_api, name='facility_geojson_api'),
]
