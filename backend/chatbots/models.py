from django.db import models
from django.conf import settings
import uuid
import secrets
from botman_backend.managers import TenantAwareManager

def generate_secret_key():
    return secrets.token_urlsafe(32)

class Chatbot(models.Model):
    LLM_CHOICES = [
        ('openai', 'OpenAI'),
        ('gemini', 'Gemini'),
    ]

    BOT_TYPE_CHOICES = [
        ('sales', 'Sales Bot'),
        ('support', 'Support Bot'),
        ('marketing', 'Marketing Bot'),
        ('faq', 'FAQ Bot'),
        ('custom', 'Custom Bot'),
    ]

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    system_prompt = models.TextField(default="You are a helpful AI assistant.", blank=True)
    selected_llm = models.CharField(max_length=50, choices=LLM_CHOICES, default='gemini')
    
    # Personality & Behavior
    bot_type = models.CharField(max_length=50, choices=BOT_TYPE_CHOICES, default='custom')
    personality = models.TextField(blank=True, help_text="The personality of the bot (e.g. friendly, professional)")
    tone = models.CharField(max_length=100, blank=True, help_text="The tone of the bot (e.g. formal, casual)")
    fallback_behavior = models.TextField(blank=True, help_text="What to say when the bot doesn't know the answer")

    # Security & Widget Configuration
    widget_token = models.UUIDField(default=uuid.uuid4, editable=False, help_text="Public Key for the widget")
    secret_key = models.CharField(max_length=100, default=generate_secret_key, editable=False, help_text="Secret Key for backend verification")
    allowed_domains = models.TextField(default="*", help_text="Comma-separated list of allowed domains (e.g. example.com, mysite.org). Use * for all.")
    
    # Status
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    published_config = models.JSONField(default=dict, blank=True)
    bot_prompt_config = models.JSONField(default=dict, blank=True, help_text="Configuration for system prompt, personality, fallback, and guardrails.")
    
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chatbots')
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantAwareManager()

    def get_runtime_config(self):
        """
        Returns the published configuration if available, otherwise falls back to current model fields.
        """
        if self.is_published and self.published_config:
            return self.published_config
        # Fallback to current fields (e.g. for preview or if never published but forced)
        return {
            'name': self.name,
            'description': self.description,
            'system_prompt': self.system_prompt,
            'selected_llm': self.selected_llm,
            'allowed_domains': self.allowed_domains,
            'bot_prompt_config': self.bot_prompt_config,
            'bot_type': self.bot_type,
            'personality': self.personality,
            'tone': self.tone,
            'fallback_behavior': self.fallback_behavior
        }

    def __str__(self):
        return self.name
