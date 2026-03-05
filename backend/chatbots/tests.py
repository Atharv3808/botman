from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Chatbot
from unittest.mock import patch
from knowledge.models import KnowledgeFile, KnowledgeChunk

User = get_user_model()

class ChatbotSystemPromptTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.chatbot = Chatbot.objects.create(
            name='Test Bot',
            owner=self.user,
            system_prompt='Original prompt'
        )
        self.url = f'/api/chatbots/{self.chatbot.id}/'

    def test_update_system_prompt(self):
        new_prompt = 'Updated system prompt'
        data = {'system_prompt': new_prompt}
        response = self.client.patch(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.chatbot.refresh_from_db()
        self.assertEqual(self.chatbot.system_prompt, new_prompt)

    def test_retrieve_chatbot_includes_system_prompt(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['system_prompt'], 'Original prompt')

    def test_studio_includes_system_prompt(self):
        studio_url = f'/api/chatbots/{self.chatbot.id}/studio/'
        response = self.client.get(studio_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['system_prompt'], 'Original prompt')
        self.assertIn('stats', response.data)

class TestMessageEndpointTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.chatbot = Chatbot.objects.create(
            name='Test Bot',
            owner=self.user
        )
        self.url = f'/api/chatbots/{self.chatbot.id}/test-message/'

    @patch('chatbots.views.process_chat_message')
    def test_test_message_endpoint(self, mock_process_chat_message):
        # Setup mock return value
        mock_process_chat_message.return_value = ("Bot response", type('obj', (object,), {'id': 1}))
        
        data = {
            'message': 'Hello',
            'visitor_id': 'test-visitor'
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify process_chat_message was called with preview_mode=True
        mock_process_chat_message.assert_called_once()
        args, kwargs = mock_process_chat_message.call_args
        self.assertEqual(kwargs['preview_mode'], True)
        self.assertEqual(kwargs['stream'], True)

class ChatbotPublishTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.chatbot = Chatbot.objects.create(
            name='Test Bot',
            owner=self.user
        )
        self.url = f'/api/chatbots/{self.chatbot.id}/publish/'

    def test_publish_returns_correct_script(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        token = response.data['widget_token']
        expected_script = f'<script src="https://botman-widget.com/widget.js" data-bot="{token}"></script>'
        self.assertEqual(response.data['embed_script'], expected_script)
        self.assertTrue(response.data['is_published'])
        self.assertIn('secret_key', response.data)
        
        self.chatbot.refresh_from_db()
        self.assertTrue(self.chatbot.is_published)
        self.assertTrue(self.chatbot.is_active)

    def test_publish_freezes_config(self):
        self.chatbot.system_prompt = "Original Prompt"
        self.chatbot.save()
        
        # Publish
        self.client.post(self.url)
        self.chatbot.refresh_from_db()
        
        # Verify snapshot
        self.assertEqual(self.chatbot.published_config['system_prompt'], "Original Prompt")
        
        # Update draft
        self.chatbot.system_prompt = "New Draft Prompt"
        self.chatbot.save()
        
        # Verify snapshot is still original
        self.assertEqual(self.chatbot.published_config['system_prompt'], "Original Prompt")
        self.assertEqual(self.chatbot.system_prompt, "New Draft Prompt")
        
        # Verify get_runtime_config returns snapshot
        config = self.chatbot.get_runtime_config()
        self.assertEqual(config['system_prompt'], "Original Prompt")

class StudioApiTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.chatbot = Chatbot.objects.create(
            name='Studio Bot',
            owner=self.user,
            selected_llm='openai'
        )
        self.knowledge_file = KnowledgeFile.objects.create(chatbot=self.chatbot, status='completed')
        self.chunk = KnowledgeChunk.objects.create(
            chatbot=self.chatbot, 
            knowledge_file=self.knowledge_file,
            content="test",
            embedding=[0.1]*1536
        )

    def test_get_studio_aggregated_data(self):
        url = f'/api/chatbots/{self.chatbot.id}/studio/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['stats']['knowledge_files'], 1)
        self.assertEqual(response.data['stats']['total_chunks'], 1)

    def test_update_settings(self):
        url = f'/api/chatbots/{self.chatbot.id}/settings/'
        data = {
            'name': 'New Name',
            'description': 'New Desc',
            'system_prompt': 'New Prompt'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.chatbot.refresh_from_db()
        self.assertEqual(self.chatbot.name, 'New Name')
        self.assertEqual(self.chatbot.description, 'New Desc')
        self.assertEqual(self.chatbot.system_prompt, 'New Prompt')

    def test_update_provider(self):
        url = f'/api/chatbots/{self.chatbot.id}/provider/'
        data = {'selected_llm': 'gemini'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.chatbot.refresh_from_db()
        self.assertEqual(self.chatbot.selected_llm, 'gemini')

    def test_update_provider_invalid(self):
        url = f'/api/chatbots/{self.chatbot.id}/provider/'
        data = {'selected_llm': 'invalid'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_knowledge(self):
        url = f'/api/chatbots/{self.chatbot.id}/knowledge/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
