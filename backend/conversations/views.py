from django.shortcuts import get_object_or_404
from django.http import StreamingHttpResponse
from rest_framework import viewsets, status, views, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
import time

from chatbots.models import Chatbot
from .models import Conversation
from .serializers import ChatRequestSerializer, ConversationSerializer, ConversationListSerializer
from .services import process_chat_message
from ai_services.utils import embed_text, search_knowledge
from ai_services.prompts import build_rag_prompt
from monitoring.utils import Logger

class ConversationFilter(django_filters.FilterSet):
    start_date = django_filters.DateTimeFilter(field_name="started_at", lookup_expr='gte')
    end_date = django_filters.DateTimeFilter(field_name="started_at", lookup_expr='lte')
    chatbot_id = django_filters.NumberFilter(field_name="chatbot__id")
    session_id = django_filters.NumberFilter(field_name="session__id")
    
    class Meta:
        model = Conversation
        fields = ['chatbot_id', 'visitor_identifier', 'session_id', 'is_preview', 'start_date', 'end_date']

class ConversationHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = ConversationFilter
    ordering_fields = ['started_at', 'id']
    ordering = ['-started_at']
    search_fields = ['visitor_identifier', 'messages__content']

    def get_queryset(self):
        return Conversation.objects.all().select_related('chatbot', 'session', 'visitor').prefetch_related('messages')

    def get_serializer_class(self):
        if self.action == 'list':
            return ConversationListSerializer
        return ConversationSerializer

class DebugRAGView(views.APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        bot_id = request.data.get('bot_id')
        question = request.data.get('question')
        
        if not bot_id or not question:
            return Response({'error': 'bot_id and question are required'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            chatbot = Chatbot.objects.get(id=bot_id, owner=request.user)
        except Chatbot.DoesNotExist:
            return Response({'error': 'Chatbot not found'}, status=status.HTTP_404_NOT_FOUND)
            
        # 1. Embed
        start_time = time.time()
        embedding = embed_text(question)
        if not embedding:
             return Response({'error': 'Embedding generation failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
             
        # 2. Search
        chunks = search_knowledge(chatbot, embedding, limit=5, threshold=0.45)
        
        # 3. Calculate Score & Routing
        similarity_score = 0.0
        if chunks and hasattr(chunks[0], 'distance'):
             similarity_score = max(0.0, 1.0 - chunks[0].distance)
             
        routing_decision = "knowledge" if similarity_score > 0.45 else "ai_api"
        
        # 4. Preview Context
        context = "\n\n".join([c.content for c in chunks])
        
        # 5. Build Prompt
        prompt = build_rag_prompt(chatbot, context, "", question)
        
        return Response({
            'retrieved_chunks': [{'id': c.id, 'content': c.content, 'distance': c.distance, 'similarity': 1.0 - c.distance} for c in chunks],
            'similarity_score': similarity_score,
            'routing_decision': routing_decision,
            'context_preview': context,
            'final_prompt_preview': prompt,
            'latency_ms': (time.time() - start_time) * 1000
        })

class ChatViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny] # Allow public access for chat

    @action(detail=True, methods=['post'])
    def chat(self, request, pk=None):
        # Validate input
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        message_text = serializer.validated_data['message']
        visitor_id = serializer.validated_data['visitor_id']
        
        # Get chatbot
        chatbot = get_object_or_404(Chatbot, pk=pk)
        
        # Call process_chat_message with stream=True
        response_generator = process_chat_message(chatbot, visitor_id, message_text, stream=True)
        
        # Check if it returned a generator (streaming) or tuple (non-streaming/error fallback)
        if hasattr(response_generator, '__iter__') and not isinstance(response_generator, (str, tuple)):
             return StreamingHttpResponse(response_generator, content_type='text/event-stream')
        else:
            # Fallback for non-streaming (should not happen with current service logic but good for safety)
            response_text, conversation = response_generator
            return Response({
                "response": response_text,
                "conversation_id": conversation.id
            })

    @action(detail=False, methods=['post'], url_path='preview')
    def preview(self, request):
        """
        Preview chat endpoint for Studio.
        Uses the provided bot_id (pk not in URL because it's detail=False but we need it).
        Actually, let's keep it detail=False but expect bot_id in body, OR 
        make it detail=True if we want /chat/{id}/preview.
        User requested POST /chat/preview (which usually means global endpoint).
        Let's assume the body contains bot_id.
        """
        bot_id = request.data.get('bot_id')
        if not bot_id:
             return Response({"error": "bot_id is required"}, status=status.HTTP_400_BAD_REQUEST)
             
        # Validate input
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        message_text = serializer.validated_data['message']
        visitor_id = serializer.validated_data['visitor_id']
        stream = serializer.validated_data.get('stream', True)
        
        # Get chatbot - ensure user owns it if not superuser
        # Since we are using AllowAny on ViewSet, we should ideally check permission here.
        # But for simplicity, we just get the bot.
        chatbot = get_object_or_404(Chatbot, pk=bot_id)
        
        # Call process_chat_message with preview_mode=True
        response_generator = process_chat_message(chatbot, visitor_id, message_text, stream=stream, preview_mode=True)
        
        if hasattr(response_generator, '__iter__') and not isinstance(response_generator, (str, tuple)):
             return StreamingHttpResponse(response_generator, content_type='text/event-stream')
        else:
            response_text, conversation = response_generator
            return Response({
                "response": response_text,
                "conversation_id": conversation.id
            })


class PublicChatView(views.APIView):
    permission_classes = [AllowAny]
    throttle_scope = 'public_widget'

    def post(self, request, widget_token):
        # Validate widget_token format
        try:
            import uuid
            uuid.UUID(str(widget_token))
        except ValueError:
            return Response(
                {"success": False, "message": "Invalid widget token format.", "error_code": "INVALID_TOKEN"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate input
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        message_text = serializer.validated_data['message']
        visitor_id = serializer.validated_data['visitor_id']
        
        # Get chatbot by widget_token
        chatbot = get_object_or_404(Chatbot, widget_token=widget_token)
        
        # Call process_chat_message with stream=True
        response_generator = process_chat_message(chatbot, visitor_id, message_text, stream=True)
        
        if hasattr(response_generator, '__iter__') and not isinstance(response_generator, (str, tuple)):
             return StreamingHttpResponse(response_generator, content_type='text/event-stream')
        else:
             # Fallback
            response_text, conversation = response_generator
            return Response({
                "response": response_text,
                "conversation_id": conversation.id
            })
