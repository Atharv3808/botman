from django.db import models
from .tenant_context import get_current_tenant

class TenantAwareManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        tenant = get_current_tenant()
        user_id = tenant.get('user_id')
        bot_id = tenant.get('bot_id')
        is_superuser = tenant.get('is_superuser', False)
        
        # Superusers see everything
        if is_superuser:
            return queryset
            
        if user_id:
            # Filter by Owner/User (Tenant)
            if hasattr(self.model, 'owner'):
                # Check if owner is a User
                # Ideally we check isinstance(field, ForeignKey) and related_model is User
                # But simple check is okay for now
                queryset = queryset.filter(owner_id=user_id)
            elif hasattr(self.model, 'user'):
                # Common pattern: user field points to the owner
                queryset = queryset.filter(user_id=user_id)
            elif hasattr(self.model, 'chatbot'):
                # Assuming chatbot has owner
                queryset = queryset.filter(chatbot__owner_id=user_id)
            elif hasattr(self.model, 'conversation'):
                # Assuming conversation -> chatbot -> owner
                queryset = queryset.filter(conversation__chatbot__owner_id=user_id)
        
        # Filter by Bot (Sub-Tenant/Resource)
        if bot_id:
            if self.model.__name__ == 'Chatbot':
                 queryset = queryset.filter(id=bot_id)
            elif hasattr(self.model, 'chatbot'):
                 queryset = queryset.filter(chatbot_id=bot_id)
            elif hasattr(self.model, 'conversation'):
                 queryset = queryset.filter(conversation__chatbot_id=bot_id)

        return queryset
