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

        # Log to database
        # Skip logging for high-frequency or public widget endpoints to avoid unnecessary DB writes
        # Especially to prevent Live Server infinite reload loops in development
        skip_paths = ['/widget/config/', '/api/health/']
        if any(request.path.startswith(path) for path in skip_paths):
            return response

        # We wrap in try-except to ensure logging failure doesn't break the response
        try:
            RequestLog.objects.create(
                endpoint=request.path,
                method=request.method,
                user=user,
                response_status=response.status_code,
                response_time=response_time_ms,
                ip_address=ip
            )
        except Exception as e:
            # In a real production app, we might log this error to a file or sentry
            print(f"Error logging request: {e}")

        return response
