from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django.http import StreamingHttpResponse
from django.core import signing
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from chatbots.models import Chatbot
from conversations.services import process_chat_message
from conversations.models import Session, Conversation
import uuid
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class OriginValidationPermission(permissions.BasePermission):
    """
    Validates that the request origin is allowed for the chatbot.
    """
    def has_permission(self, request, view):
        return True

def validate_origin(request, chatbot):
    config = chatbot.get_runtime_config()
    allowed_domains = config.get('allowed_domains', '*')
    
    # In development, we might want to be more lenient
    if settings.DEBUG:
        return True

    # Get origin from header, fallback to Referer if Origin is missing (some browsers/scenarios)
    origin = request.headers.get('Origin') or request.headers.get('Referer')
    
    if not origin:
        # If still no origin/referer, only allow if domains is *
        return allowed_domains == '*'
    
    if allowed_domains == '*':
        return True
        
    allowed = [d.strip().lower() for d in allowed_domains.split(',')]
    
    try:
        parsed_origin = urlparse(origin)
        domain = parsed_origin.netloc.lower()
        # Remove port if present
        if ':' in domain:
            domain = domain.split(':')[0]
        
        # Check for direct match or subdomain match if allowed starts with .
        for a in allowed:
            if domain == a:
                return True
            if a.startswith('.') and domain.endswith(a):
                return True
    except Exception as e:
        logger.error(f"Error parsing origin {origin}: {e}")
        return False
        
    return False

def validate_bot_status(chatbot):
    if not chatbot.is_active:
        return False, "Bot is inactive."
    if not chatbot.is_published:
        return False, "Bot is not published."
    return True, None

class WidgetConfigView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'public_widget'

    def get(self, request, widget_token):
        chatbot = get_object_or_404(Chatbot, widget_token=widget_token)
        
        is_valid, error_msg = validate_bot_status(chatbot)
        if not is_valid:
            return Response({"error": error_msg}, status=status.HTTP_403_FORBIDDEN)
            
        if not validate_origin(request, chatbot):
            return Response({"error": "Origin not allowed"}, status=status.HTTP_403_FORBIDDEN)
            
        config = chatbot.get_runtime_config()
        
        return Response({
            "id": chatbot.id,
            "name": config.get('name'),
            "description": config.get('description'),
            "initial_message": config.get('fallback_behavior') or "Hello! How can I help you today?",
            "widget_token": str(chatbot.widget_token),
            "theme": {
                "primary_color": "#10b981",
                "position": "right",
                "welcome_message": f"Hi! I'm {chatbot.name}. How can I help?",
                "avatar_url": None
            }
        })

class WidgetSessionView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'public_widget'

    def post(self, request):
        # Prefer widget_token for security, fallback to bot_id for internal tests
        widget_token = request.data.get('bot_token')
        bot_id = request.data.get('bot_id')
        
        if widget_token:
            chatbot = get_object_or_404(Chatbot, widget_token=widget_token)
        elif bot_id:
            chatbot = get_object_or_404(Chatbot, id=bot_id)
        else:
            return Response({"error": "bot_token or bot_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        is_valid, error_msg = validate_bot_status(chatbot)
        if not is_valid:
            return Response({"error": error_msg}, status=status.HTTP_403_FORBIDDEN)
            
        if not validate_origin(request, chatbot):
            return Response({"error": "Origin not allowed"}, status=status.HTTP_403_FORBIDDEN)
            
        visitor_id = str(uuid.uuid4())
        session_token = signing.dumps({'visitor_id': visitor_id, 'bot_id': chatbot.id})
        
        return Response({
            "session_token": session_token,
            "visitor_id": visitor_id
        })

class WidgetChatView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'public_widget'

    def post(self, request):
        session_token = request.data.get('session_token')
        message = request.data.get('message')
        
        if not session_token or not message:
            return Response({"error": "session_token and message are required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            data = signing.loads(session_token, max_age=86400)
            visitor_id = data['visitor_id']
            bot_id = data['bot_id']
        except signing.BadSignature:
             return Response({"error": "Invalid or expired session token"}, status=status.HTTP_401_UNAUTHORIZED)
             
        chatbot = get_object_or_404(Chatbot, id=bot_id)
        
        is_valid, error_msg = validate_bot_status(chatbot)
        if not is_valid:
            return Response({"error": error_msg}, status=status.HTTP_403_FORBIDDEN)
            
        if not validate_origin(request, chatbot):
             return Response({"error": "Origin not allowed"}, status=status.HTTP_403_FORBIDDEN)
             
        response_generator = process_chat_message(chatbot, visitor_id, message, stream=True)
        
        if hasattr(response_generator, '__iter__') and not isinstance(response_generator, (str, tuple)):
             return StreamingHttpResponse(response_generator, content_type='text/event-stream')
        else:
            response_text, conversation = response_generator
            return Response({
                "response": response_text,
                "conversation_id": conversation.id
            })
