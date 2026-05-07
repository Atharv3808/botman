import time
from .models import RequestLog

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        
        # Process the request
        response = self.get_response(request)
        
        # Calculate duration
        duration = time.time() - start_time
        response_time_ms = duration * 1000

        # Extract user
        user = request.user if request.user.is_authenticated else None

        # Extract IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        # Log to database asynchronously
        # Skip logging for high-frequency or public widget endpoints to avoid unnecessary DB writes
        skip_paths = ['/widget/config/', '/api/health/', '/static/', '/media/']
        if any(request.path.startswith(path) for path in skip_paths):
            return response

        from .tasks import log_request_async
        
        log_data = {
            'endpoint': request.path,
            'method': request.method,
            'response_status': response.status_code,
            'response_time': response_time_ms,
            'ip_address': ip,
            'user_id': user.id if user else None
        }

        try:
            log_request_async.delay(log_data)
        except Exception as e:
            # Fallback if celery is not running
            print(f"Error queuing request log: {e}")

        return response
