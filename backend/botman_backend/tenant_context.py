import threading
from contextlib import contextmanager

_thread_locals = threading.local()

def get_current_tenant():
    """
    Returns a dictionary with the current tenant context.
    Keys: user_id, bot_id, workspace_id, is_superuser
    """
    return getattr(_thread_locals, 'tenant_context', {})

def set_tenant_context(user_id=None, bot_id=None, workspace_id=None, is_superuser=False):
    """
    Sets the current tenant context.
    """
    _thread_locals.tenant_context = {
        'user_id': user_id,
        'bot_id': bot_id,
        'workspace_id': workspace_id,
        'is_superuser': is_superuser
    }

def clear_tenant_context():
    """
    Clears the tenant context.
    """
    _thread_locals.tenant_context = {}

@contextmanager
def tenant_context(user_id=None, bot_id=None, workspace_id=None, is_superuser=False):
    """
    Context manager to temporarily set tenant context.
    """
    previous_context = get_current_tenant()
    set_tenant_context(user_id, bot_id, workspace_id, is_superuser)
    try:
        yield
    finally:
        _thread_locals.tenant_context = previous_context
