from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db import connections
from django.db.utils import OperationalError
from django.conf import settings
import redis
from celery.result import AsyncResult
from ai_services.llm import call_openai

class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        health_status = {
            "db_connected": False,
            "redis_connected": False,
            "celery_active": False,
            "ai_provider_reachable": False
        }

        # Check Database
        try:
            db_conn = connections['default']
            db_conn.cursor()
            health_status["db_connected"] = True
        except OperationalError:
            health_status["db_connected"] = False

        # Check Redis
        try:
            # Parse Redis URL to get connection details
            redis_url = settings.CELERY_BROKER_URL
            r = redis.from_url(redis_url)
            r.ping()
            health_status["redis_connected"] = True
        except Exception:
            health_status["redis_connected"] = False

        # Check Celery
        # We can check celery status by inspecting active workers and queue length
        try:
            from botman_backend.celery import app
            
            # Check queue length via Redis
            redis_url = settings.CELERY_BROKER_URL
            r = redis.from_url(redis_url)
            queue_length = r.llen('celery')
            health_status["celery_queue_length"] = queue_length
            
            # Check active workers
            i = app.control.inspect()
            if i.ping():
                health_status["celery_active"] = True
            else:
                 health_status["celery_active"] = False
        except Exception:
            health_status["celery_active"] = False
            health_status["celery_queue_length"] = -1

        # Check AI Provider (OpenAI as default)
        try:
             # We'll make a very cheap/simple call or just check if API key is set 
             # and maybe try to list models if possible, but list models is also an API call.
             # Let's try a minimal chat completion or just check env var + connectivity.
             # For a robust check, we should make a real call.
             # Using a dummy prompt.
             
             # Note: Making a real API call every health check might be expensive/slow.
             # Ideally we cache this or just check if the service is reachable (ping google.com?)
             # But the requirement says "ai provider reachable".
             # Let's try a very small request.
             
             # Since call_openai is available, let's use it but with a tiny prompt.
             # If we want to avoid cost, we could just check if we can reach the API endpoint.
             # For now, let's assume we want to verify credentials too.
             
             # Optimization: Maybe just check if the API Key is present for a "liveness" check,
             # and do a real call for a "readiness" check. 
             # But the prompt implies a status report. 
             # Let's do a simple connection check or catch the exception from a call.
             
             # To avoid cost, we can just check if we can import and setup the client 
             # and maybe ping the base URL if possible.
             # But `call_openai` does a generation.
             
             # Let's mock it for now if it's too expensive, or just check env vars.
             # However, "reachable" implies network connectivity to the provider.
             import requests
             response = requests.get("https://api.openai.com/v1/models", headers={
                 "Authorization": f"Bearer {settings.OPENAI_API_KEY}"
             }, timeout=5)
             
             if response.status_code == 200:
                 health_status["ai_provider_reachable"] = True
             else:
                 # If we get 401 (invalid key) or 200, it's reachable. 
                 # If 401, it is reachable but unauthorized. 
                 # Let's count any response as reachable.
                 health_status["ai_provider_reachable"] = True
                 
        except Exception:
             health_status["ai_provider_reachable"] = False

        return Response(health_status, status=status.HTTP_200_OK)
