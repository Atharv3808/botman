
from rest_framework import serializers
from .models import Conversation, Message, Session, Visitor
from chatbots.models import Chatbot

class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(required=True, allow_blank=False, min_length=1)
    visitor_id = serializers.CharField(required=True)
    stream = serializers.BooleanField(required=False, default=True)

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'sender', 'content', 'created_at', 'latency', 'token_usage', 'source']

class ChatbotSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chatbot
        fields = ['id', 'name']

class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    chatbot = ChatbotSimpleSerializer(read_only=True)
    session_id = serializers.IntegerField(source='session.id', read_only=True)
    visitor_external_id = serializers.CharField(source='visitor.external_id', read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'chatbot', 'visitor_identifier', 'visitor_external_id', 'session_id', 'is_preview', 'started_at', 'messages']

class ConversationListSerializer(serializers.ModelSerializer):
    chatbot = ChatbotSimpleSerializer(read_only=True)
    session_id = serializers.IntegerField(source='session.id', read_only=True)
    visitor_external_id = serializers.CharField(source='visitor.external_id', read_only=True)
    message_count = serializers.IntegerField(source='messages.count', read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'chatbot', 'visitor_identifier', 'visitor_external_id', 'session_id', 'is_preview', 'started_at', 'message_count']
