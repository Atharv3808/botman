
from django.db import models
from chatbots.models import Chatbot
from botman_backend.managers import TenantAwareManager

class Visitor(models.Model):
    external_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.external_id

class Session(models.Model):
    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE, related_name='sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Session {self.id} for {self.visitor}"

class Conversation(models.Model):
    chatbot = models.ForeignKey(Chatbot, on_delete=models.CASCADE, related_name='conversations')
    visitor_identifier = models.CharField(max_length=255) # Renamed from visitor_id to avoid clash
    visitor = models.ForeignKey(Visitor, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations')
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations')
    is_preview = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)

    objects = TenantAwareManager()

    def __str__(self):
        return f"Conversation with {self.visitor_identifier} on {self.chatbot.name}"

class Message(models.Model):
    SENDER_CHOICES = [
        ('user', 'User'),
        ('bot', 'Bot'),
    ]

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Metrics
    latency = models.FloatField(null=True, blank=True, help_text="Latency in milliseconds")
    token_usage = models.IntegerField(default=0, help_text="Total tokens used for this response")
    source = models.CharField(max_length=50, null=True, blank=True, help_text="Source of the response (e.g. knowledge, ai_api)")
    confidence_score = models.FloatField(null=True, blank=True, help_text="Confidence score of the knowledge retrieval (0-1)")

    objects = TenantAwareManager()

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender}: {self.content[:50]}"
