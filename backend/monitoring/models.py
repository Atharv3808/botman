from django.db import models

class SystemLog(models.Model):
    LEVEL_CHOICES = [
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    CATEGORY_CHOICES = [
        ('AI', 'AI Service'),
        ('EMBEDDING', 'Embedding Service'),
        ('WIDGET', 'Widget'),
        ('SYSTEM', 'System'),
        ('DB', 'Database'),
    ]
    
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='INFO')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='SYSTEM')
    message = models.TextField()
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional context (JSON)")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['level', 'category']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"[{self.created_at}] {self.level} - {self.category}: {self.message[:50]}"
