from django.contrib import admin
from .models import TelegramIntegration

@admin.register(TelegramIntegration)
class TelegramIntegrationAdmin(admin.ModelAdmin):
    list_display = ('chatbot', 'telegram_bot_username', 'is_active', 'created_at')
    search_fields = ('chatbot__name', 'telegram_bot_username')
    list_filter = ('is_active', 'created_at')
    readonly_fields = ('webhook_url', 'created_at')

    def get_queryset(self, request):
        # Admin should see everything
        return TelegramIntegration.objects.all()
