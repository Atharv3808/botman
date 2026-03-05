from django.db import models
from django.conf import settings
from chatbots.models import Chatbot
from botman_backend.managers import TenantAwareManager

class RequestLog(models.Model):
    endpoint = models.CharField(max_length=255)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    response_status = models.IntegerField()
    response_time = models.FloatField(help_text="Response time in milliseconds")
    timestamp = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=10)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.method} {self.endpoint} - {self.response_status} ({self.response_time}ms)"

    class Meta:
        ordering = ['-timestamp']

class TokenUsage(models.Model):
    chatbot = models.ForeignKey(Chatbot, on_delete=models.CASCADE, related_name='token_usages')
    provider = models.CharField(max_length=50) # 'openai', 'gemini'
    tokens_input = models.IntegerField(default=0)
    tokens_output = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    objects = TenantAwareManager()

    def __str__(self):
        return f"{self.chatbot.name} - {self.provider}: {self.total_tokens} tokens"

class BotAnalyticsDaily(models.Model):
    chatbot = models.ForeignKey(Chatbot, on_delete=models.CASCADE, related_name='daily_analytics')
    date = models.DateField()
    total_messages = models.IntegerField(default=0)
    active_sessions = models.IntegerField(default=0)
    avg_latency = models.FloatField(default=0.0, help_text="Average latency in ms")
    total_tokens = models.IntegerField(default=0)
    knowledge_hit_rate = models.FloatField(default=0.0, help_text="Percentage of messages from knowledge base (0-100)")

    objects = TenantAwareManager()

    class Meta:
        unique_together = ('chatbot', 'date')
        verbose_name_plural = "Bot Analytics Daily"
    
    def __str__(self):
        return f"{self.chatbot.name} - {self.date}"
