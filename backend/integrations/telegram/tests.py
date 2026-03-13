from rest_framework.test import APIClient, APITestCase
from django.urls import reverse
from unittest.mock import patch, MagicMock
from chatbots.models import Chatbot
from accounts.models import User
from .models import TelegramIntegration
from .utils import encrypt_token, decrypt_token
import json

class TelegramIntegrationTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password", first_name="Test User")
        self.chatbot = Chatbot.objects.create(name="Test Bot", owner=self.user)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch('integrations.telegram.services.TelegramService.verify_telegram_token')
    @patch('integrations.telegram.services.TelegramService.set_telegram_webhook')
    def test_connect_telegram_bot(self, mock_set_webhook, mock_verify_token):
        mock_verify_token.return_value = {"username": "test_bot"}
        mock_set_webhook.return_value = True

        url = reverse('telegram_connect')
        data = {
            "bot_id": self.chatbot.id,
            "telegram_bot_token": "123456:ABC"
        }
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(TelegramIntegration.objects.filter(chatbot=self.chatbot).exists())
        integration = TelegramIntegration.objects.get(chatbot=self.chatbot)
        self.assertEqual(integration.telegram_bot_username, "test_bot")
        self.assertEqual(integration.telegram_bot_token, "123456:ABC")

    @patch('integrations.telegram.services.TelegramService.process_telegram_message')
    @patch('integrations.telegram.services.TelegramService.send_telegram_message')
    def test_telegram_webhook(self, mock_send_message, mock_process_message):
        webhook_url = "https://example.com/api/integrations/telegram/webhook/1/?secret=test_secret"
        integration = TelegramIntegration.objects.create(
            chatbot=self.chatbot,
            telegram_bot_token_encrypted=encrypt_token("123456:ABC"),
            telegram_bot_username="test_bot",
            webhook_url=webhook_url,
            is_active=True
        )
        mock_process_message.return_value = "Hello from AI"
        mock_send_message.return_value = True

        # Correct secret
        url = reverse('telegram_webhook', kwargs={'bot_id': self.chatbot.id}) + "?secret=test_secret"
        data = {
            "message": {
                "chat": {"id": 12345},
                "text": "Hello bot"
            }
        }
        client = APIClient()
        response = client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # Wrong secret
        url_wrong = reverse('telegram_webhook', kwargs={'bot_id': self.chatbot.id}) + "?secret=wrong_secret"
        response = client.post(url_wrong, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_token_encryption(self):
        token = "123456:ABC-DEF-GHI"
        encrypted = encrypt_token(token)
        self.assertNotEqual(token, encrypted)
        decrypted = decrypt_token(encrypted)
        self.assertEqual(token, decrypted)
