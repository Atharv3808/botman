from django.urls import path
from .views import ConnectTelegramBotView, TelegramWebhookView

urlpatterns = [
    path('connect/', ConnectTelegramBotView.as_view(), name='telegram_connect'),
    path('webhook/<int:bot_id>/', TelegramWebhookView.as_view(), name='telegram_webhook'),
]
