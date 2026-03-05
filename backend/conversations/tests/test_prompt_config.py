from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from chatbots.models import Chatbot
from conversations.services import process_chat_message
from unittest.mock import patch, MagicMock

User = get_user_model()

class PromptConfigTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.chatbot = Chatbot.objects.create(
            name='Config Bot', 
            owner=self.user,
            system_prompt="Original System Prompt",
            bot_prompt_config={
                "personality": "Witty and Sarcastic",
                "guardrails": "No financial advice.",
                "fallback_prompt": "I have no idea, ask someone else.",
                "system_prompt": "Configured System Prompt" # Should override model field if logic prioritizes config
            }
        )

    @patch('conversations.services.embed_text')
    @patch('conversations.services.search_knowledge')
    @patch('conversations.services.call_openai')
    @override_settings(OPENAI_API_KEY='dummy')
    def test_prompt_config_injection(self, mock_openai, mock_search, mock_embed):
        # Setup: Mock RAG match to test standard prompt construction
        mock_embed.return_value = [0.1] * 1536
        
        # 1. Test with Context (RAG Mode)
        mock_chunk = MagicMock()
        mock_chunk.content = "Context data."
        mock_chunk.distance = 0.1
        mock_search.return_value = [mock_chunk]
        
        mock_openai.return_value = ("Response", {'total_tokens': 10})

        process_chat_message(self.chatbot, 'visitor_1', "Hello", stream=False)
        
        args, _ = mock_openai.call_args
        prompt = args[0]
        
        # Verify Personality
        self.assertIn("Personality:\nWitty and Sarcastic", prompt)
        # Verify Guardrails
        self.assertIn("Guardrails:\nNo financial advice.", prompt)
        # Verify System Prompt (Config should take precedence or merge? Logic says: prompt_config.get('system_prompt', chatbot.system_prompt))
        # So "Configured System Prompt" should be there.
        self.assertIn("Chatbot Instructions:\nConfigured System Prompt", prompt)
        self.assertNotIn("Original System Prompt", prompt)

    @patch('conversations.services.embed_text')
    @patch('conversations.services.search_knowledge')
    @patch('conversations.services.call_openai')
    @override_settings(OPENAI_API_KEY='dummy')
    def test_fallback_prompt_config(self, mock_openai, mock_search, mock_embed):
        # 2. Test Fallback Mode (No Context)
        mock_embed.return_value = [0.1] * 1536
        mock_search.return_value = []
        
        mock_openai.return_value = ("Response", {'total_tokens': 10})
        
        process_chat_message(self.chatbot, 'visitor_1', "Hello", stream=False)
        
        args, _ = mock_openai.call_args
        prompt = args[0]
        
        # Verify Fallback Prompt
        self.assertIn("System:\nI have no idea, ask someone else.", prompt)
        # Verify Personality is still present
        self.assertIn("Personality:\nWitty and Sarcastic", prompt)
