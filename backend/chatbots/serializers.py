from rest_framework import serializers
from .models import Chatbot

class ChatbotSerializer(serializers.ModelSerializer):
    name = serializers.CharField(min_length=3, max_length=50)

    class Meta:
        model = Chatbot
        fields = ['id', 'name', 'description', 'system_prompt', 'bot_type', 'personality', 'tone', 'fallback_behavior', 'allowed_domains', 'selected_llm', 'widget_token', 'secret_key', 'is_active', 'is_published', 'created_at']
        read_only_fields = ['id', 'widget_token', 'secret_key', 'is_published', 'created_at']

class StudioSerializer(serializers.ModelSerializer):
    knowledge_file_count = serializers.SerializerMethodField()

    class Meta:
        model = Chatbot
        fields = ['id', 'name', 'description', 'system_prompt', 'selected_llm', 'widget_token', 'knowledge_file_count']

    def get_knowledge_file_count(self, obj):
        return obj.files.count()
