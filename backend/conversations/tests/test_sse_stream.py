from django.test import TestCase
from unittest.mock import patch, MagicMock
from conversations.services import stream_response_generator
from conversations.models import Conversation, Chatbot, Visitor
from django.contrib.auth import get_user_model
import json

class SSEStreamTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.chatbot = Chatbot.objects.create(
            name="Test Bot",
            system_prompt="You are a helper.",
            selected_llm="openai",
            owner=self.user
        )
        self.visitor = Visitor.objects.create(external_id="test_visitor")
        self.conversation = Conversation.objects.create(
            chatbot=self.chatbot,
            visitor=self.visitor,
            visitor_identifier="test_visitor"
        )

    @patch('conversations.services.call_openai')
    def test_openai_stream_sse_format(self, mock_call_openai):
        # Mock OpenAI response chunks
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock()]
        chunk1.choices[0].delta.content = "Hello"
        
        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta.content = " World"
        
        chunk3 = MagicMock()
        chunk3.choices = [MagicMock()]
        chunk3.choices[0].delta.content = None # End of stream or usage chunk
        chunk3.usage = MagicMock()
        chunk3.usage.prompt_tokens = 10
        chunk3.usage.completion_tokens = 5
        chunk3.usage.total_tokens = 15

        mock_call_openai.return_value = [chunk1, chunk2, chunk3]

        generator = stream_response_generator(
            self.chatbot, 
            "Test Prompt", 
            self.conversation, 
            start_time=0
        )

        results = list(generator)
        
        # Verify SSE format
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], 'data: {"content": "Hello"}\n\n')
        self.assertEqual(results[1], 'data: {"content": " World"}\n\n')

    @patch('conversations.services.call_gemini')
    def test_gemini_stream_sse_format(self, mock_call_gemini):
        self.chatbot.selected_llm = 'gemini'
        
        # Mock Gemini response chunks
        chunk1 = MagicMock()
        chunk1.text = "Hi"
        
        chunk2 = MagicMock()
        chunk2.text = " there"
        
        # Mock response object that is iterable
        mock_response = MagicMock()
        mock_response.__iter__.return_value = [chunk1, chunk2]
        mock_response.usage_metadata.prompt_token_count = 10
        mock_response.usage_metadata.candidates_token_count = 5
        mock_response.usage_metadata.total_token_count = 15
        
        # When iterating, it should return chunks. 
        # But in services.py: 
        # response_stream = call_gemini(...)
        # for chunk in response_stream: ...
        # if hasattr(response_stream, 'usage_metadata'): ...
        
        # So call_gemini should return the mock_response which is iterable
        mock_call_gemini.return_value = mock_response

        generator = stream_response_generator(
            self.chatbot, 
            "Test Prompt", 
            self.conversation, 
            start_time=0
        )

        results = list(generator)
        
        # Verify SSE format
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], 'data: {"content": "Hi"}\n\n')
        self.assertEqual(results[1], 'data: {"content": " there"}\n\n')

    @patch('conversations.services.call_openai')
    def test_openai_stream_error(self, mock_call_openai):
        # Mock Error
        mock_call_openai.return_value = "OpenAI Error"

        generator = stream_response_generator(
            self.chatbot, 
            "Test Prompt", 
            self.conversation, 
            start_time=0
        )

        results = list(generator)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], 'event: error\ndata: {"message": "OpenAI Error"}\n\n')
