
import os
import django
from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'botman_backend.settings.dev')
django.setup()

from knowledge.models import KnowledgeChunk
chunk = KnowledgeChunk.objects.first()
if chunk:
    print(f"Type: {type(chunk.embedding)}")
    print(f"Value sample: {chunk.embedding[:5] if chunk.embedding else 'None'}")
else:
    print("No chunks found")
