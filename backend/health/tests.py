from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

class HealthCheckTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/health'

    @override_settings(OPENAI_API_KEY='dummy')
    @patch('health.views.connections')
    @patch('health.views.redis.from_url')
    @patch('botman_backend.celery.app.control.inspect')
    @patch('requests.get')
    def test_health_check_success(self, mock_get, mock_inspect, mock_redis, mock_connections):
        # Mock DB
        mock_conn = MagicMock()
        mock_connections.__getitem__.return_value = mock_conn
        
        # Mock Redis
        mock_r = MagicMock()
        mock_redis.return_value = mock_r
        
        # Mock Celery
        mock_i = MagicMock()
        mock_i.ping.return_value = {'celery@worker': {'ok': 'pong'}}
        mock_inspect.return_value = mock_i
        
        # Mock AI
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Configure mock to return response when called
        mock_get.return_value = mock_response

        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['db_connected'])
        self.assertTrue(response.data['redis_connected'])
        self.assertTrue(response.data['celery_active'])
        self.assertTrue(response.data['ai_provider_reachable'])

    @patch('health.views.connections')
    def test_health_check_db_fail(self, mock_connections):
        from django.db.utils import OperationalError
        mock_connections.__getitem__.side_effect = OperationalError("DB Error")
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['db_connected'])
