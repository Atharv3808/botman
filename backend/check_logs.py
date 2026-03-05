
import os
import django
from dotenv import load_dotenv

# Load env vars first
load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'botman_backend.settings.dev')
django.setup()

from monitoring.models import SystemLog

print("--- Recent Logs ---")
for log in SystemLog.objects.order_by('-created_at')[:10]:
    print(f'{log.level} - {log.category}: {log.message}')
