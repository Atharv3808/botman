from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core import signing
from rest_framework import status
from chatbots.models import Chatbot
from unittest.mock import patch
import uuid

User = get_user_model()

class WidgetApiTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.chatbot = Chatbot.objects.create(
            name='Widget Bot',
            owner=self.user,
            allowed_domains='example.com, my-site.org',
            is_published=True,
            is_active=True
        )
        self.client = Client()

    def test_config_endpoint_unpublished_bot(self):
        self.chatbot.is_published = False
        self.chatbot.save()
        url = f'/widget/config/{self.chatbot.id}/'
        response = self.client.get(url, HTTP_ORIGIN='https://example.com')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_config_endpoint_inactive_bot(self):
        self.chatbot.is_active = False
        self.chatbot.save()
        url = f'/widget/config/{self.chatbot.id}/'
        response = self.client.get(url, HTTP_ORIGIN='https://example.com')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_config_endpoint_valid_origin(self):
        url = f'/widget/config/{self.chatbot.id}/'
        # Mock Origin header
        response = self.client.get(url, HTTP_ORIGIN='https://example.com')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Widget Bot')

    def test_config_endpoint_invalid_origin(self):
        url = f'/widget/config/{self.chatbot.id}/'
        response = self.client.get(url, HTTP_ORIGIN='https://evil.com')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_config_endpoint_wildcard_origin(self):
        self.chatbot.allowed_domains = '*'
        self.chatbot.published_config = {
            'name': 'Widget Bot',
            'description': '',
            'system_prompt': '',
            'selected_llm': 'openai',
            'allowed_domains': '*'
        }
        self.chatbot.save()
        url = f'/widget/config/{self.chatbot.id}/'
        response = self.client.get(url, HTTP_ORIGIN='https://anywhere.com')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_config_uses_snapshot(self):
        # Set published config
        self.chatbot.published_config = {
            'name': 'Published Name',
            'description': 'Published Desc',
            'allowed_domains': 'example.com'
        }
        self.chatbot.save()
        
        # Change draft
        self.chatbot.name = "Draft Name"
        self.chatbot.save()
        
        url = f'/widget/config/{self.chatbot.id}/'
        response = self.client.get(url, HTTP_ORIGIN='https://example.com')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Published Name')

    def test_session_endpoint(self):
        url = '/widget/session/'
        data = {'bot_id': self.chatbot.id}
        response = self.client.post(url, data, content_type='application/json', HTTP_ORIGIN='https://example.com')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('session_token', response.data)
        self.assertIn('visitor_id', response.data)
        
        # Verify token
        token = response.data['session_token']
        payload = signing.loads(token)
        self.assertEqual(payload['bot_id'], self.chatbot.id)

    def test_chat_endpoint_valid_token(self):
        # Create session
        visitor_id = str(uuid.uuid4())
        token = signing.dumps({'visitor_id': visitor_id, 'bot_id': self.chatbot.id})
        
        url = '/widget/chat/'
        data = {'session_token': token, 'message': 'Hello'}
        
        with patch('widgets.views.process_chat_message') as mock_process:
            mock_process.return_value = ("Bot response", type('obj', (object,), {'id': 1}))
            
            response = self.client.post(url, data, content_type='application/json', HTTP_ORIGIN='https://example.com')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['response'], 'Bot response')
            
            mock_process.assert_called_once()
            args, kwargs = mock_process.call_args
            self.assertEqual(args[1], visitor_id) # visitor_id
            self.assertEqual(args[2], 'Hello') # message

    def test_chat_endpoint_invalid_token(self):
        url = '/widget/chat/'
        data = {'session_token': 'invalid_token', 'message': 'Hello'}
        response = self.client.post(url, data, content_type='application/json', HTTP_ORIGIN='https://example.com')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
