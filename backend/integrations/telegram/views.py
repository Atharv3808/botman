from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django.conf import settings
from chatbots.models import Chatbot
from .models import TelegramIntegration
from .services import TelegramService
from monitoring.utils import Logger
import json

from .tasks import process_telegram_message_task
from .utils import encrypt_token

class ConnectTelegramBotView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        bot_id = request.data.get("bot_id")
        token = request.data.get("telegram_bot_token")

        if not bot_id or not token:
            return Response({"error": "bot_id and telegram_bot_token are required"}, status=status.HTTP_400_BAD_REQUEST)

        chatbot = get_object_or_404(Chatbot, id=bot_id, owner=request.user)

        # 1. Validate token
        bot_info = TelegramService.verify_telegram_token(token)
        if not bot_info:
            return Response({"error": "Invalid Telegram Bot Token"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Register Webhook
        base_url = settings.BASE_URL or request.build_absolute_uri('/')[:-1]
        
        # Security check: Telegram requires HTTPS for webhooks.
        if base_url.startswith('http://') and 'localhost' not in base_url and '127.0.0.1' not in base_url:
             # Most production/public non-localhost URLs must be HTTPS.
             # However, Telegram strictly forbids any HTTP for webhooks.
             pass

        if not base_url.startswith('https://'):
            Logger.warning("TELEGRAM", f"Webhook base_url is not HTTPS: {base_url}. Telegram might reject this.")

        # Add a secret to the webhook URL for validation
        import secrets
        webhook_secret = secrets.token_urlsafe(16)
        webhook_url = f"{base_url}/api/integrations/telegram/webhook/{chatbot.id}/?secret={webhook_secret}"
        
        success = TelegramService.set_telegram_webhook(token, webhook_url)
        if not success:
            # Check the system log for detailed error
            from monitoring.models import SystemLog
            last_error = SystemLog.objects.filter(category='TELEGRAM', level='ERROR').order_by('-id').first()
            error_msg = f"Failed to set Telegram webhook. {last_error.message if last_error else ''}"
            return Response({"error": error_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 3. Save integration
        # Use encrypt_token directly as update_or_create works on database fields
        integration, created = TelegramIntegration.objects.update_or_create(
            chatbot=chatbot,
            defaults={
                "telegram_bot_token_encrypted": encrypt_token(token),
                "telegram_bot_username": bot_info.get("username"),
                "webhook_url": webhook_url,
                "is_active": True
            }
        )

        return Response({
            "message": "Telegram bot connected successfully",
            "bot_username": bot_info.get("username"),
            "webhook_url": webhook_url
        }, status=status.HTTP_200_OK)

class TelegramWebhookView(APIView):
    permission_classes = [permissions.AllowAny] # Telegram sends webhooks without auth header

    def post(self, request, bot_id):
        chatbot = get_object_or_404(Chatbot, id=bot_id)
        integration = getattr(chatbot, 'telegram_integration', None)

        if not integration or not integration.is_active:
            Logger.warning("TELEGRAM", f"Received webhook for inactive or non-existent integration for Bot {bot_id}")
            return Response({"error": "Integration not active"}, status=status.HTTP_403_FORBIDDEN)

        # Validate secret from URL
        webhook_secret = request.query_params.get("secret")
        # Extract secret from saved webhook_url
        saved_secret = None
        if integration.webhook_url and "?secret=" in integration.webhook_url:
            saved_secret = integration.webhook_url.split("?secret=")[-1]
        
        if not webhook_secret or webhook_secret != saved_secret:
            Logger.warning("TELEGRAM", f"Invalid secret for webhook for Bot {bot_id}")
            return Response({"error": "Invalid secret"}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        Logger.info("TELEGRAM", f"Received webhook data for Bot {bot_id}", data)

        if "message" in data:
            message = data["message"]
            chat_id = message["chat"]["id"]
            text = message.get("text")

            if text:
                # Send the message to the background task for processing
                process_telegram_message_task.send(bot_id, chat_id, text)

        # Return a 200 OK response immediately
        return Response({"status": "ok"}, status=status.HTTP_200_OK)
