from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from chatbots.models import Chatbot
from conversations.services import process_chat_message
from conversations.models import Message
from unittest.mock import patch, MagicMock

User = get_user_model()

class AgentRoutingTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.chatbot = Chatbot.objects.create(name='Routing Bot', owner=self.user)
    
    @patch('conversations.services.embed_text')
    @patch('conversations.services.search_knowledge')
    @patch('conversations.services.call_openai')
    @override_settings(OPENAI_API_KEY='dummy')
    def test_high_confidence_rag_routing(self, mock_openai, mock_search, mock_embed):
        # Setup: High confidence match
        mock_embed.return_value = [0.1] * 1536
        
        mock_chunk = MagicMock()
        mock_chunk.content = "Relevant context."
        mock_chunk.distance = 0.1 # Similarity = 0.9
        mock_search.return_value = [mock_chunk]
        
        mock_openai.return_value = ("Answer from context", {'total_tokens': 10})
        
        # Action
        process_chat_message(self.chatbot, 'visitor_1', "Query", stream=False)
        
        # Verify
        message = Message.objects.last()
        self.assertEqual(message.source, 'knowledge')
        self.assertAlmostEqual(message.confidence_score, 0.9)
        
        # Check prompt contains context
        args, _ = mock_openai.call_args
        prompt = args[0]
        self.assertIn("Context Information:", prompt)
        self.assertIn("Relevant context.", prompt)

    @patch('conversations.services.embed_text')
    @patch('conversations.services.search_knowledge')
    @patch('conversations.services.call_openai')
    @override_settings(OPENAI_API_KEY='dummy')
    def test_fallback_ai_provider_routing(self, mock_openai, mock_search, mock_embed):
        # Setup: No match (search returns empty)
        mock_embed.return_value = [0.1] * 1536
        mock_search.return_value = [] # Below threshold
        
        mock_openai.return_value = ("General knowledge answer", {'total_tokens': 10})
        
        # Action
        process_chat_message(self.chatbot, 'visitor_1', "Query", stream=False)
        
        # Verify
        message = Message.objects.last()
        self.assertEqual(message.source, 'ai_api')
        self.assertEqual(message.confidence_score, 0.0)
        
        # Check prompt uses fallback system instruction
        args, _ = mock_openai.call_args
        prompt = args[0]
        self.assertNotIn("Context Information:", prompt)
        self.assertIn("using your general knowledge", prompt)
