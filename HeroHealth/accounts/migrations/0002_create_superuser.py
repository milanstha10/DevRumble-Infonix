from django.db import migrations
from django.contrib.auth.hashers import make_password

def create_superuser(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    
    # Create the superuser only if it doesn't already exist
    if not User.objects.filter(username='admin').exists():
        User.objects.create(
            username='admin',
            email='admin@herohealth.com',
            password=make_password('admin123'),
            is_superuser=True,
            is_staff=True,
            is_active=True
        )

def remove_superuser(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    User.objects.filter(username='admin').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_superuser, reverse_code=remove_superuser),
    ]
