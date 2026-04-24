from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import ProviderConfiguration, ProviderAuditLog
from .utils import encrypt_data, decrypt_data

User = get_user_model()

class ProviderConfigurationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='password', role='admin')

    def test_encryption_decryption(self):
        data = "test-api-key-123"
        encrypted = encrypt_data(data)
        self.assertNotEqual(data, encrypted)
        decrypted = decrypt_data(encrypted)
        self.assertEqual(data, decrypted)

    def test_provider_config_creation(self):
        config = ProviderConfiguration.objects.create(
            provider_type='openai',
            name='Test OpenAI',
            created_by=self.user
        )
        credentials = {'api_key': 'sk-12345'}
        config.set_credentials(credentials)
        config.save()

        # Check retrieval
        config.refresh_from_db()
        self.assertEqual(config.get_credentials(), credentials)
        self.assertEqual(config.version, 1)

    def test_audit_logging(self):
        ProviderAuditLog.objects.create(
            user=self.user,
            provider_name='Test Provider',
            action='create',
            status='success'
        )
        self.assertEqual(ProviderAuditLog.objects.count(), 1)
        log = ProviderAuditLog.objects.first()
        self.assertEqual(log.action, 'create')

from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

class ProviderAPITest(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(username='admin2', password='password', role='admin')
        self.client.force_authenticate(user=self.admin_user)

    def test_create_provider_api(self):
        url = reverse('provider-configuration-list')
        data = {
            'provider_type': 'openai',
            'name': 'API OpenAI',
            'credentials': {'api_key': 'sk-test'},
            'config_data': {'default_model': 'gpt-4o'}
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProviderConfiguration.objects.count(), 1)
        
    def test_update_versioning_api(self):
        config = ProviderConfiguration.objects.create(
            provider_type='openai',
            name='Old Name',
            created_by=self.admin_user
        )
        url = reverse('provider-configuration-detail', args=[config.id])
        data = {'name': 'New Name'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should have 2 versions now
        self.assertEqual(ProviderConfiguration.objects.count(), 2)
        new_version = ProviderConfiguration.objects.get(is_active=True)
        self.assertEqual(new_version.name, 'New Name')
        self.assertEqual(new_version.version, 2)
        
        old_version = ProviderConfiguration.objects.get(id=config.id)
        self.assertFalse(old_version.is_active)

    def test_regular_user_permissions(self):
        regular_user = User.objects.create_user(username='regular', password='password', role='user')
        self.client.force_authenticate(user=regular_user)
        
        # Should be able to list
        url = reverse('provider-configuration-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should NOT be able to create
        data = {
            'provider_type': 'openai',
            'name': 'Unauthorized OpenAI',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Should NOT be able to test connection
        config = ProviderConfiguration.objects.create(
            provider_type='openai',
            name='Test Config',
            created_by=self.admin_user
        )
        test_url = reverse('provider-configuration-test-connection', args=[config.id])
        response = self.client.post(test_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
