
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import StreamingHttpResponse
from django.utils import timezone
from .models import Chatbot
from .serializers import ChatbotSerializer, StudioSerializer
from conversations.serializers import ChatRequestSerializer
from conversations.services import process_chat_message
import uuid
from accounts.models import Subscription, Plan

class ChatbotViewSet(viewsets.ModelViewSet):
    serializer_class = ChatbotSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return chatbots owned by the current user
        return Chatbot.objects.filter(owner=self.request.user)

    def create(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            bot_count = Chatbot.objects.filter(owner=user).count()
            try:
                subscription = user.subscription
            except Subscription.DoesNotExist:
                # If no subscription, create a free one
                free_plan = Plan.objects.get(name='Free')
                subscription = Subscription.objects.create(user=user, plan=free_plan)
            
            if subscription.plan and bot_count >= subscription.plan.bot_limit:
                return Response(
                    {"error": "Bot limit reached. Upgrade your plan to create more bots."},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        # Automatically set the owner to the current user
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['get'])
    def studio(self, request, pk=None):
        chatbot = self.get_object()
        serializer = StudioSerializer(chatbot)
        
        # Aggregate data
        from knowledge.models import KnowledgeFile, KnowledgeChunk
        knowledge_files_count = KnowledgeFile.objects.filter(chatbot=chatbot).count()
        total_chunks = KnowledgeChunk.objects.filter(chatbot=chatbot).count()
        
        data = serializer.data
        data['stats'] = {
            'knowledge_files': knowledge_files_count,
            'total_chunks': total_chunks
        }
        return Response(data)

    @action(detail=True, methods=['post', 'patch'], url_path='settings')
    def update_settings(self, request, pk=None):
        chatbot = self.get_object()
        # Allow updating name, description, system_prompt, allowed_domains
        allowed_fields = ['name', 'description', 'system_prompt', 'allowed_domains']
        for field in allowed_fields:
            if field in request.data:
                setattr(chatbot, field, request.data[field])
        chatbot.save()
        return Response(ChatbotSerializer(chatbot).data)

    @action(detail=True, methods=['post'])
    def provider(self, request, pk=None):
        chatbot = self.get_object()
        # Allow updating selected_llm
        if 'selected_llm' in request.data:
            # Validate choice
            valid_choices = [c[0] for c in Chatbot.LLM_CHOICES]
            if request.data['selected_llm'] not in valid_choices:
                return Response({"error": "Invalid LLM provider"}, status=status.HTTP_400_BAD_REQUEST)
            chatbot.selected_llm = request.data['selected_llm']
            chatbot.save()
        return Response(ChatbotSerializer(chatbot).data)

    @action(detail=True, methods=['get', 'post'])
    def knowledge(self, request, pk=None):
        chatbot = self.get_object()
        from knowledge.models import KnowledgeFile
        from knowledge.serializers import KnowledgeFileSerializer
        
        if request.method == 'POST':
            # Handle upload
            # We need to inject chatbot into the data or serializer context
            # Serializer expects 'chatbot' field usually
            data = request.data.copy()
            data['chatbot'] = chatbot.id
            
            serializer = KnowledgeFileSerializer(data=data)
            if serializer.is_valid():
                # Save file
                instance = serializer.save()
                
                # Trigger async processing
                from ai_services.tasks import process_knowledge_file
                process_knowledge_file.delay(instance.id)
                
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # GET
        files = KnowledgeFile.objects.filter(chatbot=chatbot).order_by('-uploaded_at')
        return Response(KnowledgeFileSerializer(files, many=True).data)

    @action(detail=True, methods=['post'], url_path='test-message')
    def test_message(self, request, pk=None):
        chatbot = self.get_object()
        
        # Validate input
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        message_text = serializer.validated_data['message']
        visitor_id = serializer.validated_data['visitor_id']
        
        # Call process_chat_message with stream=True and preview_mode=True
        response_generator = process_chat_message(chatbot, visitor_id, message_text, stream=True, preview_mode=True)
        
        if hasattr(response_generator, '__iter__') and not isinstance(response_generator, (str, tuple)):
             return StreamingHttpResponse(response_generator, content_type='text/event-stream')
        else:
            # Fallback
            response_text, conversation = response_generator
            return Response({
                "response": response_text,
                "conversation_id": conversation.id
            })

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        chatbot = self.get_object()
        
        # Freeze config snapshot
        config_snapshot = {
            'name': chatbot.name,
            'description': chatbot.description,
            'system_prompt': chatbot.system_prompt,
            'selected_llm': chatbot.selected_llm,
            'allowed_domains': chatbot.allowed_domains,
            'published_at': str(timezone.now())
        }
        chatbot.published_config = config_snapshot
        
        # Set published status
        chatbot.is_published = True
        chatbot.is_active = True
        chatbot.save()
            
        token = str(chatbot.widget_token)
        # Use request host if available, but normalize localhost to 127.0.0.1 for local dev stability
        host = request.get_host()
        if host.startswith('localhost'):
            host = host.replace('localhost', '127.0.0.1')
        base_url = f"{request.scheme}://{host}"
        embed_script = f"""<script src="{base_url}/static/widgets/widget.js" data-bot-id="{token}" async></script>"""
        
        return Response({
            "widget_token": token,
            "secret_key": chatbot.secret_key,
            "embed_script": embed_script,
            "is_published": True
        })
