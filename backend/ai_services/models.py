from django.db import models
from django.conf import settings
import json
from .utils import encrypt_data, decrypt_data

class ProviderConfiguration(models.Model):
    PROVIDER_CHOICES = (
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic'),
        ('google', 'Google AI'),
        ('azure', 'Azure OpenAI'),
        ('custom', 'Custom Provider'),
    )

    provider_type = models.CharField(max_length=50, choices=PROVIDER_CHOICES)
    name = models.CharField(max_length=100)
    config_data = models.JSONField(default=dict)  # Stores non-sensitive data
    encrypted_credentials = models.TextField(blank=True, null=True)  # Stores encrypted sensitive data
    is_active = models.BooleanField(default=True)
    version = models.IntegerField(default=1)
    parent_config = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='versions')
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_credentials(self, credentials_dict):
        """Encrypts and sets the credentials."""
        json_data = json.dumps(credentials_dict)
        self.encrypted_credentials = encrypt_data(json_data)

    def get_credentials(self):
        """Decrypts and returns the credentials."""
        if not self.encrypted_credentials:
            return {}
        decrypted_json = decrypt_data(self.encrypted_credentials)
        return json.loads(decrypted_json)

    def __str__(self):
        return f"{self.get_provider_type_display()} - {self.name} (v{self.version})"

    class Meta:
        ordering = ['-updated_at']

class ProviderAuditLog(models.Model):
    ACTION_CHOICES = (
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('test', 'Test Connection'),
        ('rollback', 'Rollback'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    provider_name = models.CharField(max_length=100)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    details = models.JSONField(default=dict)
    status = models.CharField(max_length=20, default='success')  # success, failure
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action} - {self.provider_name} at {self.created_at}"

    class Meta:
        ordering = ['-created_at']
