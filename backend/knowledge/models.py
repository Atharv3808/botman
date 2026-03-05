
from django.db import models
from chatbots.models import Chatbot
from pgvector.django import VectorField
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex

class KnowledgeFile(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    chatbot = models.ForeignKey(Chatbot, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='knowledge_files/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    chunk_count = models.IntegerField(default=0)
    processing_error = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file.name} ({self.status})"

class KnowledgeChunk(models.Model):
    chatbot = models.ForeignKey(Chatbot, on_delete=models.CASCADE, related_name='chunks')
    knowledge_file = models.ForeignKey(KnowledgeFile, on_delete=models.CASCADE, related_name='chunks')
    content = models.TextField()
    chunk_index = models.IntegerField(default=0)
    embedding = VectorField(dimensions=768, null=True, blank=True) # Gemini text-embedding-004 uses 768 dimensions
    search_vector = SearchVectorField(null=True)

    class Meta:
        indexes = [
            GinIndex(fields=['search_vector']),
        ]

    def __str__(self):
        return f"Chunk {self.id} for {self.chatbot.name}"
