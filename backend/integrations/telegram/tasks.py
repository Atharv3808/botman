from celery import shared_task
from integrations.telegram.services import TelegramService
from chatbots.models import Chatbot

@shared_task
def process_telegram_message_task(bot_id, chat_id, text):
    """
    Celery task to process a Telegram message asynchronously.
    """
    try:
        chatbot = Chatbot.objects.get(id=bot_id)
        integration = getattr(chatbot, 'telegram_integration', None)

        if not integration or not integration.is_active:
            return

        # Process message through AI engine
        response_text = TelegramService.process_telegram_message(chatbot, chat_id, text)

        if response_text:
            # Send reply back to Telegram
            TelegramService.send_telegram_message(integration.telegram_bot_token, chat_id, response_text)

    except Chatbot.DoesNotExist:
        # Handle case where chatbot is not found
        pass
    except Exception as e:
        # Log any other exceptions
        print(f"Error in process_telegram_message_task: {e}")
