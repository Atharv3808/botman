from django.db import models
from chatbots.models import Chatbot
from botman_backend.managers import TenantAwareManager

from .utils import encrypt_token, decrypt_token

class TelegramIntegration(models.Model):
    id = models.BigAutoField(primary_key=True)
    chatbot = models.OneToOneField(Chatbot, on_delete=models.CASCADE, related_name='telegram_integration')
    telegram_bot_token_encrypted = models.CharField(max_length=512, unique=True)
    telegram_bot_username = models.CharField(max_length=255, blank=True, null=True)
    webhook_url = models.URLField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantAwareManager()

    @property
    def telegram_bot_token(self):
        return decrypt_token(self.telegram_bot_token_encrypted)

    @telegram_bot_token.setter
    def telegram_bot_token(self, value):
        self.telegram_bot_token_encrypted = encrypt_token(value)

    def __str__(self):
        return f"Telegram Bot: @{self.telegram_bot_username or 'unknown'} for {self.chatbot.name}"
