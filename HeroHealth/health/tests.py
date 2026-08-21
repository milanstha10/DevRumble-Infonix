from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import UserProfile
from facilities.models import HealthcareFacility
from ai_engine.safety import is_safe_query
from ai_engine.services import run_local_triage

class UserProfileTests(TestCase):
    def test_profile_creation_signal(self):
        # Create user
        user = User.objects.create_user(username='testpatient', password='password123')
        # Check profile exists
        self.assertIsNotNone(user.profile)
        self.assertEqual(user.profile.user, user)

class SafetyTriageTests(TestCase):
    def test_query_safety_validation(self):
        # Test safe input
        is_safe, err = is_safe_query("I have severe fever and cough.")
        self.assertTrue(is_safe)
        
        # Test short input
        is_safe, err = is_safe_query("bad")
        self.assertFalse(is_safe)
        self.assertIn("too short", err)

        # Test gibberish input
        is_safe, err = is_safe_query("aaaaaaaaaaa")
        self.assertFalse(is_safe)
        self.assertIn("gibberish", err)

    def test_local_triage_critical_rules(self):
        # Test urgent chest pain keywords
        result = run_local_triage("I am experiencing chest pain and shortness of breath.")
        self.assertEqual(result['severity'], 'Urgent')
        self.assertEqual(result['suggested_specialty'], 'Cardiology / Emergency Medicine')
        self.assertTrue(any("AMBULANCE" in action for action in result['recommended_actions']))

        # Test mild fever cold keywords
        result_mild = run_local_triage("I have mild cold and cough and slight throat pain.")
        self.assertEqual(result_mild['severity'], 'Medium')
        self.assertEqual(result_mild['suggested_specialty'], 'General Medicine')


class HealthChatTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='chatuser', password='password123')

    def test_chat_requires_login(self):
        response = self.client.get(reverse('chatbot'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_authenticated_user_can_send_chat_message(self):
        self.client.login(username='chatuser', password='password123')
        response = self.client.post(
            reverse('chatbot_message'),
            data='{\"message\": \"I have a mild headache today.\", \"language\": \"en\"}',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('reply', response.json())
