from django.contrib import admin
from .models import SystemLog

@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'level', 'category', 'short_message')
    list_filter = ('level', 'category', 'created_at')
    search_fields = ('message', 'metadata')
    readonly_fields = ('created_at', 'level', 'category', 'message', 'metadata')
    
    def short_message(self, obj):
        return obj.message[:100]
    short_message.short_description = 'Message'
    
    def has_add_permission(self, request):
        return False
        
    def has_change_permission(self, request, obj=None):
        return False
