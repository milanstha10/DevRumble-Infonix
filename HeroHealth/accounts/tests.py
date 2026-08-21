from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import UserProfile, ensure_user_profile


class UserProfileLifecycleTests(TestCase):
    @patch('accounts.views.send_mail')
    def test_normal_signup_creates_profile(self, send_mail):
        response = self.client.post(reverse('register'), {
            'username': 'signup-user',
            'email': 'signup@example.com',
            'first_name': 'Signup',
            'last_name': 'User',
            'password': 'StrongPass!123',
            'confirm_password': 'StrongPass!123',
        })

        self.assertRedirects(response, reverse('login'))
        user = User.objects.get(username='signup-user')
        self.assertEqual(UserProfile.objects.filter(user=user).count(), 1)
        send_mail.assert_called_once()

    def test_user_creation_creates_one_profile(self):
        user = User.objects.create_user(username='profile-user', password='password123')

        self.assertEqual(UserProfile.objects.filter(user=user).count(), 1)
        user.save()
        self.assertEqual(UserProfile.objects.filter(user=user).count(), 1)

    def test_existing_user_without_profile_is_repaired(self):
        user = User.objects.create_user(username='missing-profile', password='password123')
        UserProfile.objects.filter(user=user).delete()

        profile = ensure_user_profile(user)

        self.assertEqual(profile.user, user)
        self.assertEqual(UserProfile.objects.filter(user=user).count(), 1)

    def test_repair_profiles_command_is_idempotent(self):
        user = User.objects.create_user(username='repair-user', password='password123')
        UserProfile.objects.filter(user=user).delete()

        call_command('repair_profiles')
        call_command('repair_profiles')

        self.assertEqual(UserProfile.objects.filter(user=user).count(), 1)


class GoogleCallbackTests(TestCase):
    def setUp(self):
        self.callback_url = reverse('google_callback')
        self.token_response = Mock()
        self.token_response.raise_for_status.return_value = None
        self.token_response.json.return_value = {'access_token': 'test-access-token'}
        self.user_response = Mock()
        self.user_response.raise_for_status.return_value = None
        self.user_response.json.return_value = {
            'email': 'google-user@example.com',
            'given_name': 'Google',
            'family_name': 'User',
        }

    def _set_oauth_state(self):
        session = self.client.session
        session['google_oauth_state'] = 'test-state'
        session.save()

    @patch('accounts.views.requests.get')
    @patch('accounts.views.requests.post')
    def test_new_google_user_gets_profile(self, post, get):
        post.return_value = self.token_response
        get.return_value = self.user_response
        self._set_oauth_state()

        response = self.client.get(self.callback_url, {'state': 'test-state', 'code': 'test-code'})

        self.assertRedirects(response, reverse('home'))
        user = User.objects.get(email='google-user@example.com')
        self.assertTrue(user.profile.email_verified)
        self.assertEqual(self.client.session['_auth_user_id'], str(user.pk))

    @patch('accounts.views.requests.get')
    @patch('accounts.views.requests.post')
    def test_existing_google_user_missing_profile_is_repaired(self, post, get):
        user = User.objects.create_user(
            username='existing-google',
            email='google-user@example.com',
            password='password123',
        )
        UserProfile.objects.filter(user=user).delete()
        post.return_value = self.token_response
        get.return_value = self.user_response
        self._set_oauth_state()

        response = self.client.get(self.callback_url, {'state': 'test-state', 'code': 'test-code'})

        self.assertRedirects(response, reverse('home'))
        user.refresh_from_db()
        self.assertTrue(user.profile.email_verified)
        self.assertEqual(UserProfile.objects.filter(user=user).count(), 1)
        self.assertEqual(self.client.session['_auth_user_id'], str(user.pk))
