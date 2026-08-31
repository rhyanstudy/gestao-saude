from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from gestao.models import MedicationTransfer, CmmAdjustmentRequest, MedicationTransferItem


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(username='testuser', password='testpassword')
        User.objects.create_superuser(username='testadmin', password='testpassword')

    def test_login_page_renders(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gestao/login.html')
        self.assertContains(response, 'username_select')

    def test_login_selection_works(self):
        User.objects.create_user(username='user1', password='user123')
        response = self.client.post(reverse('login'), data={'username': 'user1'})
        self.assertEqual(response.status_code, 302)

    def test_dashboard_redirect_regular_user(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('dashboard_redirect'))
        self.assertRedirects(response, reverse('user_dashboard'))


class CmmFeatureTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_a = User.objects.create_user(username='user_a', password='password123')

        today = timezone.now().date()
        days_to_tuesday = (1 - today.weekday()) % 7 or 7
        self.tuesday = today + timedelta(days=days_to_tuesday)
        self.past_tuesday = self.tuesday - timedelta(days=14)

    def test_create_valid_cmm_auto_resolves_health_unit(self):
        self.client.login(username='user_a', password='password123')
        form_data = {
            'effective_date': self.tuesday,
            'requester_name': 'Dr. Carlos',
            'requester_role': 'Médico',
            'medication[]': ['Paracetamol 500mg'],
            'current_quantity[]': ['100'],
            'new_quantity[]': ['150'],
            'supri_code[]': ['909'],
        }
        response = self.client.post(reverse('submit_cmm_request'), data=form_data)
        self.assertRedirects(response, reverse('user_dashboard'))

        req = CmmAdjustmentRequest.objects.filter(user=self.user_a).first()
        self.assertIsNotNone(req)
        self.assertEqual(req.health_unit, 'Unidade de Saúde Padrão')

    def test_create_cmm_past_date_blocked(self):
        self.client.login(username='user_a', password='password123')
        form_data = {
            'effective_date': self.past_tuesday,
            'requester_name': 'Dr. Carlos',
            'requester_role': 'Médico',
            'medication[]': ['Paracetamol 500mg'],
            'current_quantity[]': ['100'],
            'new_quantity[]': ['150'],
            'supri_code[]': ['909'],
        }
        response = self.client.post(reverse('submit_cmm_request'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('effective_date', response.context['form'].errors)

    def test_create_cmm_invalid_supri_blocked(self):
        self.client.login(username='user_a', password='password123')
        form_data = {
            'effective_date': self.tuesday,
            'requester_name': 'Dr. Carlos',
            'requester_role': 'Médico',
            'medication[]': ['Paracetamol 500mg'],
            'current_quantity[]': ['100'],
            'new_quantity[]': ['150'],
            'supri_code[]': ['SUPRI12'],
        }
        response = self.client.post(reverse('submit_cmm_request'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CmmAdjustmentRequest.objects.filter(user=self.user_a).exists())


class MedicationTransferTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1', password='password123')

    def test_create_valid_transfer(self):
        self.client.login(username='user1', password='password123')
        form_data = {
            'observation': 'Urgente',
            'medication[]': ['Soro Fisiologico', 'Dipirona'],
            'quantity[]': ['150', '50'],
            'cmm[]': ['500', '200'],
            'supri_code[]': ['4002', '8922'],
        }
        response = self.client.post(reverse('submit_medication'), data=form_data)
        self.assertRedirects(response, reverse('user_dashboard'))

        transfer = MedicationTransfer.objects.filter(user=self.user1).first()
        self.assertIsNotNone(transfer)
        self.assertEqual(transfer.items.count(), 2)

        item1 = transfer.items.get(medication='Soro Fisiologico')
        self.assertEqual(item1.cmm, 500)
        self.assertEqual(item1.quantity, 150)

    def test_create_transfer_invalid_supri_blocked(self):
        self.client.login(username='user1', password='password123')
        form_data = {
            'observation': 'Urgente',
            'medication[]': ['Soro Fisiologico'],
            'quantity[]': ['150'],
            'cmm[]': ['500'],
            'supri_code[]': ['ABC1'],
        }
        response = self.client.post(reverse('submit_medication'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(MedicationTransfer.objects.filter(user=self.user1).exists())
