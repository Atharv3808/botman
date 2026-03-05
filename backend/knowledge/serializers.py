from rest_framework import serializers
from .models import KnowledgeFile
import os

class KnowledgeFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeFile
        fields = ['id', 'chatbot', 'file', 'status', 'chunk_count', 'processing_error', 'uploaded_at']
        read_only_fields = ['status', 'chunk_count', 'processing_error', 'uploaded_at']

    def validate_file(self, value):
        # 1. Check file size (limit: 10MB)
        limit_mb = 10
        if value.size > limit_mb * 1024 * 1024:
            raise serializers.ValidationError(f"File size too large. Size should not exceed {limit_mb} MB.")

        # 2. Check file extension
        ext = os.path.splitext(value.name)[1].lower()
        valid_extensions = ['.pdf', '.txt', '.docx']
        if ext not in valid_extensions:
            raise serializers.ValidationError(f"Unsupported file extension. Allowed extensions are: {', '.join(valid_extensions)}")

        return value
