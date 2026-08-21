from django.test import TestCase
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
