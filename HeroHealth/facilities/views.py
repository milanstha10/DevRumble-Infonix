from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse
from .models import HealthcareFacility
from .services import load_facilities_from_json

def ensure_data_loaded():
    # Helper to load data dynamically if database is empty
    if HealthcareFacility.objects.count() == 0:
        try:
            load_facilities_from_json()
        except Exception as e:
            print("Failed to auto-load facilities JSON:", e)

def facility_list(request):
    ensure_data_loaded()
    query = request.GET.get('q', '').strip()
    fac_type = request.GET.get('type', '').strip()
    specialty = request.GET.get('specialty', '').strip()

    facilities = HealthcareFacility.objects.all()

    if query:
        facilities = facilities.filter(name__icontains=query) | facilities.filter(address__icontains=query)
    
    if fac_type:
        facilities = facilities.filter(type=fac_type)

    if specialty:
        facilities = facilities.filter(specializations_raw__icontains=specialty)

    # Get distinct types and specialities for filters
    all_facilities = HealthcareFacility.objects.all()
    types = all_facilities.values_list('type', flat=True).distinct()
    
    # Extract unique specializations list
    specialties_set = set()
    for f in all_facilities:
        specialties_set.update(f.specializations_list)
    specialties = sorted(list(specialties_set))

    context = {
        'facilities': facilities,
        'types': types,
        'specialties': specialties,
        'selected_type': fac_type,
        'selected_specialty': specialty,
        'query': query
    }
    return render(request, 'facilities/facility_list.html', context)

def facility_detail(request, pk):
    ensure_data_loaded()
    facility = get_object_or_404(HealthcareFacility, pk=pk)
    return render(request, 'facilities/facility_detail.html', {'facility': facility})

def map_view(request):
    ensure_data_loaded()
    # Extract unique specializations list for filters on the map page too
    all_facilities = HealthcareFacility.objects.all()
    specialties_set = set()
    for f in all_facilities:
        specialties_set.update(f.specializations_list)
    specialties = sorted(list(specialties_set))
    
    context = {
        'specialties': specialties,
        'selected_specialty': request.GET.get('specialty', '')
    }
    return render(request, 'facilities/map.html', context)

def facility_geojson_api(request):
    ensure_data_loaded()
    specialty = request.GET.get('specialty', '').strip()
    facilities = HealthcareFacility.objects.all()
    
    if specialty:
        facilities = facilities.filter(specializations_raw__icontains=specialty)
        
    features = []
    for f in facilities:
        features.append({
            'type': 'Feature',
            'properties': {
                'id': f.id,
                'name': f.name,
                'type': f.type,
                'address': f.address,
                'phone': f.phone or 'N/A',
                'website': f.website or '',
                'specializations': f.specializations_list,
                'status': f.status,
                'detail_url': reverse('facility_detail', args=[f.id])
            },
            'geometry': {
                'type': 'Point',
                'coordinates': [f.longitude, f.latitude] # GeoJSON coordinates are [lon, lat]
            }
        })
        
    return JsonResponse({
        'type': 'FeatureCollection',
        'features': features
    })
