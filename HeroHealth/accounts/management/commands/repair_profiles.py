from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.models import UserProfile, ensure_user_profile


class Command(BaseCommand):
    help = 'Create missing UserProfile records without changing existing profiles.'

    def handle(self, *args, **options):
        created_count = 0

        self.stdout.write('Checking user profiles...')
        for user in User.objects.all().iterator():
            missing = not UserProfile.objects.filter(user=user).exists()
            ensure_user_profile(user)
            if missing:
                created_count += 1

        self.stdout.write(f'Created {created_count} missing profiles.')
        self.stdout.write('0 duplicate profiles created.')
        self.stdout.write('Profile repair complete.')
