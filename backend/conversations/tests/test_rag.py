from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from chatbots.models import Chatbot
from knowledge.models import KnowledgeFile, KnowledgeChunk
from conversations.services import process_chat_message
from conversations.models import Conversation, Message
from unittest.mock import patch, MagicMock

User = get_user_model()

class RAGRetrievalTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.chatbot = Chatbot.objects.create(name='RAG Bot', owner=self.user)
        self.conversation = Conversation.objects.create(chatbot=self.chatbot, visitor_identifier='visitor_1')
        
        # Create knowledge chunk
        self.file = KnowledgeFile.objects.create(chatbot=self.chatbot, status='ready')
        self.chunk = KnowledgeChunk.objects.create(
            chatbot=self.chatbot,
            knowledge_file=self.file,
            content="Botman is an AI platform.",
            embedding=[0.1] * 1536
        )

    @patch('conversations.services.embed_text')
    @patch('conversations.services.search_knowledge')
    @patch('conversations.services.call_openai')
    @override_settings(OPENAI_API_KEY='dummy')
    def test_rag_context_injection(self, mock_openai, mock_search, mock_embed):
        # Mock embedding
        mock_embed.return_value = [0.1] * 1536
        
        # Mock search result (simulating top_k=3, threshold pass)
        mock_chunk = MagicMock()
        mock_chunk.content = "Botman is an AI platform."
        mock_chunk.distance = 0.1  # Low distance = High similarity
        mock_search.return_value = [mock_chunk]
        
        # Mock LLM response
        mock_openai.return_value = ("Botman is an AI platform.", {'total_tokens': 10})
        
        # Call process_chat_message
        response, conv = process_chat_message(self.chatbot, 'visitor_1', "What is Botman?", stream=False)
        
        # Check if context was retrieved and injected (implicitly by checking if search was called)
        mock_search.assert_called_once()
        args, kwargs = mock_search.call_args
        self.assertEqual(kwargs['limit'], 3)
        self.assertEqual(kwargs['threshold'], 0.7)
        
        # Check response
        self.assertEqual(response, "Botman is an AI platform.")
        
        # Verify Message Metrics
        bot_message = Message.objects.filter(conversation=conv, sender='bot').last()
        self.assertEqual(bot_message.source, 'knowledge')
        self.assertEqual(bot_message.token_usage, 10)
        self.assertIsNotNone(bot_message.latency)

    @patch('conversations.services.embed_text')
    @patch('conversations.services.search_knowledge')
    @patch('conversations.services.call_openai')
    @override_settings(OPENAI_API_KEY='dummy')
    def test_rag_fallback_no_context(self, mock_openai, mock_search, mock_embed):
        # Mock embedding
        mock_embed.return_value = [0.1] * 1536
        
        # Mock search result (empty list - nothing passed threshold)
        mock_search.return_value = []
        
        # Mock LLM response
        mock_openai.return_value = ("I don't know.", {'total_tokens': 10})
        
        # Call process_chat_message
        response, conv = process_chat_message(self.chatbot, 'visitor_1', "Unknown question", stream=False)
        
        # Check search called but returned empty
        mock_search.assert_called_once()
        
        # Check response
        self.assertEqual(response, "I don't know.")
        
        # Verify Message Metrics
        bot_message = Message.objects.filter(conversation=conv, sender='bot').last()
        self.assertEqual(bot_message.source, 'ai_api')
        self.assertEqual(bot_message.token_usage, 10)
        self.assertIsNotNone(bot_message.latency)
