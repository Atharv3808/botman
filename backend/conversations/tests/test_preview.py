from django.test import TestCase
from rest_framework.test import APIClient
from chatbots.models import Chatbot
from conversations.models import Conversation, Message
from analytics.models import BotAnalyticsDaily
from analytics.tasks import aggregate_daily_analytics
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import patch, MagicMock

User = get_user_model()

class PreviewChatTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.chatbot = Chatbot.objects.create(
            name='Test Bot',
            owner=self.user,
            system_prompt='You are a helper.'
        )
        self.url = '/api/chat/preview/'

    @patch('conversations.services.embed_text')
    @patch('conversations.services.search_knowledge')
    @patch('conversations.services.call_openai')
    def test_preview_chat_creates_preview_conversation(self, mock_call_openai, mock_search, mock_embed):
        # Mock embedding
        mock_embed.return_value = [0.1] * 1536
        
        # Mock search
        mock_search.return_value = []
        
        # Mock LLM response for stream=True
        # It expects an iterator
        class MockStream:
            def __init__(self):
                chunk1 = MagicMock()
                chunk1.choices = [MagicMock(delta=MagicMock(content="Hello"))]
                chunk1.usage = None
                
                chunk2 = MagicMock()
                chunk2.choices = [MagicMock(delta=MagicMock(content=" world"))]
                # Mock usage object with integer values
                usage_mock = MagicMock()
                usage_mock.prompt_tokens = 5
                usage_mock.completion_tokens = 5
                usage_mock.total_tokens = 10
                chunk2.usage = usage_mock
                
                self.chunks = [chunk1, chunk2]
            def __iter__(self):
                return iter(self.chunks)
                
        mock_call_openai.return_value = MockStream()
        
        data = {
            'bot_id': self.chatbot.id,
            'message': 'Hello preview',
            'visitor_id': 'temp-visitor-123'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, 200)
        
        # Check conversation
        conversation = Conversation.objects.get(visitor_identifier='temp-visitor-123')
        self.assertTrue(conversation.is_preview)
        
        # Check message created
        # Since it is streaming, the message is created AFTER iteration.
        # But StreamingHttpResponse iterates it.
        # However, Django Test Client might NOT iterate streaming response fully unless we consume it.
        # We need to consume the response content.
        list(response.streaming_content)
        
        message = Message.objects.get(conversation=conversation, content='Hello world')
        self.assertTrue(message)

    def test_analytics_ignores_preview(self):
        # Create a regular conversation
        Conversation.objects.create(
            chatbot=self.chatbot,
            visitor_identifier='regular-visitor',
            is_preview=False
        )
        # Create a preview conversation
        Conversation.objects.create(
            chatbot=self.chatbot,
            visitor_identifier='preview-visitor',
            is_preview=True
        )
        
        # Create messages for both
        regular_conv = Conversation.objects.get(visitor_identifier='regular-visitor')
        Message.objects.create(conversation=regular_conv, content='hi', sender='user', token_usage=10)
        
        preview_conv = Conversation.objects.get(visitor_identifier='preview-visitor')
        Message.objects.create(conversation=preview_conv, content='hi preview', sender='user', token_usage=10)
        
        # Run aggregation
        aggregate_daily_analytics(timezone.now().date().strftime('%Y-%m-%d'))
        
        # Check analytics
        stats = BotAnalyticsDaily.objects.get(chatbot=self.chatbot, date=timezone.now().date())
        
        # Should only count the regular message
        self.assertEqual(stats.total_messages, 1)
        self.assertEqual(stats.total_tokens, 10) 
