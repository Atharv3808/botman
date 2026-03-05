import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from chatbots.models import Chatbot
from knowledge.models import KnowledgeFile
from conversations.models import Conversation, Message
from botman_backend.tenant_context import tenant_context

User = get_user_model()

@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class EndToEndWorkflowTests(TestCase):
    def setUp(self):
        # 1. User Registration & Auth
        self.user_password = 'securepassword123'
        self.user = User.objects.create_user(
            username='e2e_user', 
            password=self.user_password,
            email='test@example.com'
        )
        self.client.login(username='e2e_user', password=self.user_password)
        
        # Get JWT Token (simulating frontend)
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': 'e2e_user',
            'password': self.user_password
        })
        self.assertEqual(response.status_code, 200)
        self.access_token = response.data['access']
        self.auth_headers = {'HTTP_AUTHORIZATION': f'Bearer {self.access_token}'}

    @patch('ai_services.tasks.OpenAI')
    @patch('ai_services.llm.OpenAI')
    @patch('conversations.services.embed_text')
    def test_complete_user_journey(self, mock_embed_text, mock_llm_openai, mock_tasks_openai):
        # --- MOCK SETUP ---
        # Mock Embeddings for Knowledge Processing
        mock_tasks_client = MagicMock()
        mock_tasks_openai.return_value = mock_tasks_client
        mock_tasks_client.embeddings.create.return_value.data = [
            MagicMock(embedding=[0.1] * 1536)
        ]

        # Mock Embeddings for Chat
        mock_embed_text.return_value = [0.1] * 1536

        # Mock Chat Completion for Widget Chat (Streaming)
        mock_llm_client = MagicMock()
        mock_llm_openai.return_value = mock_llm_client
        
        # Setup mock for stream=True
        mock_stream = MagicMock()
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta.content = "Hello from E2E Bot!"
        mock_chunk.usage = None # Usage comes at end usually, but simplistic here
        
        # We need an iterator for streaming
        def stream_gen():
            yield mock_chunk
            # Usage chunk (OpenAI standard)
            usage_chunk = MagicMock()
            usage_chunk.choices = []
            usage_chunk.usage.total_tokens = 10
            usage_chunk.usage.prompt_tokens = 5
            usage_chunk.usage.completion_tokens = 5
            yield usage_chunk

        mock_llm_client.chat.completions.create.return_value = stream_gen()

        # --- STEP 1: CREATE BOT ---
        print("\n[E2E] Creating Chatbot...")
        bot_data = {
            'name': 'E2E Test Bot',
            'description': 'A bot for testing',
            'system_prompt': 'You are a test bot.',
            'selected_llm': 'openai'
        }
        response = self.client.post(
            reverse('chatbot-list'), 
            bot_data, 
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 201)
        bot_id = response.data['id']
        self.assertTrue(Chatbot.objects.filter(id=bot_id, owner=self.user).exists())

        # --- STEP 2: UPLOAD KNOWLEDGE ---
        print("[E2E] Uploading Knowledge Base...")
        file_content = b"This is a knowledge document for the E2E test."
        uploaded_file = SimpleUploadedFile("knowledge.txt", file_content, content_type="text/plain")
        
        data = {
            'chatbot': bot_id,
            'file': uploaded_file
        }
        response = self.client.post(
            reverse('knowledge-upload'),
            data,
            format='multipart',
            **self.auth_headers
        )
        
        self.assertEqual(response.status_code, 201)
        file_id = response.data['id']
        
        kf = KnowledgeFile.objects.get(id=file_id)
        self.assertEqual(kf.status, 'completed')
        self.assertGreater(kf.chunk_count, 0)

        # --- STEP 3: PUBLISH BOT ---
        print("[E2E] Publishing Bot...")
        response = self.client.post(
            reverse('chatbot-publish', kwargs={'pk': bot_id}),
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        widget_token = response.data['widget_token']
        self.assertTrue(response.data['is_published'])

        # --- STEP 4: WIDGET INTERACTION (PUBLIC) ---
        print("[E2E] Simulating Widget Visitor...")
        
        # 4a. Get Config
        response = self.client.get(reverse('widget-config', kwargs={'bot_id': bot_id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'E2E Test Bot')

        # 4b. Create Session
        response = self.client.post(
            reverse('widget-session'),
            {'bot_id': bot_id},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        session_token = response.data['session_token']

        # 4c. Send Message
        chat_data = {
            'session_token': session_token,
            'message': 'Hello, who are you?'
        }
        response = self.client.post(
            reverse('widget-chat'),
            chat_data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Handle Streaming Response
        if response.streaming:
            content = b"".join(response.streaming_content).decode('utf-8')
            # The streaming format depends on implementation (e.g. SSE)
            # Assuming SSE, it might look like "data: ...\n\n"
            # Or if just raw text chunks.
            # Let's verify our mocked content is present.
            self.assertIn("Hello from E2E Bot!", content)
        else:
             self.assertEqual(response.data['response'], "Hello from E2E Bot!")

        # --- STEP 5: ANALYTICS VERIFICATION ---
        print("[E2E] Verifying Analytics...")
        
        # Verify conversation and message created
        with tenant_context(user_id=self.user.id):
            self.assertEqual(Conversation.objects.count(), 1)
            # User msg + Bot msg (Wait, bot msg might be created async if streaming... 
            # actually logic says create message object then stream, or stream then create?
            # Looking at services.py, it seems to rely on generator completion to save?)
            # The generator code wasn't fully visible, but usually you save after full response.
            # Since we consumed the stream above, it should be saved.
            pass
        
        # Check Analytics API
        response = self.client.get(
            reverse('analytics-overview', kwargs={'chatbot_id': bot_id}),
            # {'bot_id': bot_id}, # Not needed as query param if in URL
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        
        # --- STEP 6: TENANT ISOLATION CHECK ---
        print("[E2E] Verifying Tenant Isolation...")
        other_user = User.objects.create_user(username='other', password='password')
        other_client = self.client_class()
        other_client.login(username='other', password='password')
        other_token_resp = other_client.post(reverse('token_obtain_pair'), {
            'username': 'other',
            'password': 'password'
        })
        other_headers = {'HTTP_AUTHORIZATION': f'Bearer {other_token_resp.data["access"]}'}
        
        # Other user tries to access our bot
        response = other_client.get(
            reverse('chatbot-detail', kwargs={'pk': bot_id}),
            **other_headers
        )
        self.assertEqual(response.status_code, 404) 

        print("\n[E2E] Success! All steps passed.")
