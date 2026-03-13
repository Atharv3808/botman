import httpx
import json
from django.conf import settings
from .models import TelegramIntegration
from conversations.services import process_chat_message
from monitoring.utils import Logger

class TelegramService:
    @staticmethod
    def verify_telegram_token(token):
        """
        Validates the Telegram Bot Token using the Telegram API.
        Returns the bot info if valid, otherwise None.
        """
        url = f"https://api.telegram.org/bot{token}/getMe"
        try:
            with httpx.Client() as client:
                response = client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        return data.get("result")
                return None
        except Exception as e:
            Logger.error("TELEGRAM", f"Error verifying token: {str(e)}")
            return None

    @staticmethod
    def set_telegram_webhook(token, webhook_url):
        """
        Registers the webhook for the Telegram Bot.
        """
        url = f"https://api.telegram.org/bot{token}/setWebhook"
        try:
            with httpx.Client() as client:
                response = client.post(url, json={"url": webhook_url})
                data = response.json()
                if response.status_code == 200:
                    if data.get("ok"):
                        return True
                
                Logger.error("TELEGRAM", f"Failed to set webhook. Status: {response.status_code}, Body: {data}")
                return False
        except Exception as e:
            Logger.error("TELEGRAM", f"Error setting webhook: {str(e)}")
            return False

    @staticmethod
    def send_telegram_message(token, chat_id, text):
        """
        Sends a message to a Telegram user.
        """
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            with httpx.Client() as client:
                response = client.post(url, json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML"
                })
                if response.status_code == 200:
                    return True
                return False
        except Exception as e:
            Logger.error("TELEGRAM", f"Error sending message: {str(e)}")
            return False

    @staticmethod
    def process_telegram_message(chatbot, telegram_user_id, message_text):
        """
        Processes a message from Telegram through the Botman AI engine.
        """
        # Telegram users are anonymous but we can use their chat_id as visitor_id
        visitor_id = f"telegram_{telegram_user_id}"
        
        # We don't support streaming for Telegram (it's webhook-based)
        # Use preview_mode=False for real usage
        response_text, _ = process_chat_message(
            chatbot=chatbot,
            visitor_id=visitor_id,
            message_text=message_text,
            stream=False,
            preview_mode=False
        )
        return response_text
