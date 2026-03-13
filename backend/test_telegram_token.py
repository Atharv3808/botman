import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'botman_backend.settings.dev')
django.setup()

from integrations.telegram.services import TelegramService
from chatbots.models import Chatbot
from integrations.telegram.models import TelegramIntegration
from integrations.telegram.utils import encrypt_token

def test_token(token):
    print(f"Verifying token: {token}")
    bot_info = TelegramService.verify_telegram_token(token)
    
    if bot_info:
        print(f"Success! Bot found: @{bot_info.get('username')}")
        print(f"Full Bot Info: {bot_info}")
        
        # Try to link it to the last created bot if none is specified
        bot = Chatbot.objects.order_by('-id').first()
        if bot:
            print(f"Linking to bot: {bot.name} (ID: {bot.id})")
            
            # For testing purposes, we'll use a mock webhook URL
            webhook_url = f"https://mock-webhook.botman.com/api/integrations/telegram/webhook/{bot.id}/?secret=test_secret"
            
            # Attempt to set webhook (might fail if not public, but we'll try)
            # success = TelegramService.set_telegram_webhook(token, webhook_url)
            # print(f"Webhook set status: {success}")
            
            integration, created = TelegramIntegration.objects.update_or_create(
                chatbot=bot,
                defaults={
                    "telegram_bot_token_encrypted": encrypt_token(token),
                    "telegram_bot_username": bot_info.get("username"),
                    "webhook_url": webhook_url,
                    "is_active": True
                }
            )
            print(f"Integration {'created' if created else 'updated'} successfully!")
        else:
            print("No chatbots found in database to link to.")
    else:
        print("Failed to verify token. Please check if the token is correct.")

if __name__ == "__main__":
    token = "8555835019:AAGjwxoIy5d1p3xh-7xTk2Is5t0Mf-T-Vrw"
    test_token(token)
