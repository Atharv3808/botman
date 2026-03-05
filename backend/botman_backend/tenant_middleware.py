from .tenant_context import set_tenant_context, clear_tenant_context

class TenantContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Set initial context
        self.set_context(request)
        
        try:
            response = self.get_response(request)
        finally:
            clear_tenant_context()
            
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        bot_id = view_kwargs.get('bot_id')
        
        # Handle cases where bot_id is passed as 'pk' (e.g. ChatbotViewSet detail)
        if not bot_id and 'pk' in view_kwargs:
            view_cls = getattr(view_func, 'cls', None)
            if view_cls and view_cls.__name__ in ['ChatbotViewSet']:
                bot_id = view_kwargs['pk']

        # Check headers and query params
        if not bot_id:
            bot_id = request.headers.get('X-Bot-ID')
        
        if not bot_id:
            bot_id = request.GET.get('bot_id')

        # Update context
        self.set_context(request, bot_id=bot_id)
        return None

    def set_context(self, request, bot_id=None):
        user_id = None
        workspace_id = None
        is_superuser = False
        
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = request.user.id
            workspace_id = request.user.id
            is_superuser = request.user.is_superuser
            
        set_tenant_context(user_id=user_id, bot_id=bot_id, workspace_id=workspace_id, is_superuser=is_superuser)
