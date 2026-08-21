import os
import json
from django.conf import settings
from .models import HealthcareFacility

def load_facilities_from_json():
    json_path = os.path.join(settings.BASE_DIR, 'data', 'facilities.json')
    if not os.path.exists(json_path):
        print(f"JSON data file not found at: {json_path}")
        return 0

    with open(json_path, 'r', encoding='utf-8') as f:
        facilities_data = json.load(f)

    count = 0
    for item in facilities_data:
        # Check if already exists
        if not HealthcareFacility.objects.filter(name=item['name']).exists():
            specializations_str = ",".join(item.get('specializations', []))
            HealthcareFacility.objects.create(
                name=item['name'],
                type=item['type'],
                address=item['address'],
                phone=item.get('phone', ''),
                website=item.get('website', ''),
                specializations_raw=specializations_str,
                latitude=item['latitude'],
                longitude=item['longitude'],
                status=item.get('status', 'Available')
            )
            count += 1
    return count
