import os
import django
import sys
from dotenv import load_dotenv

# Setup Django environment
sys.path.append(os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'botman_backend.settings.dev')
load_dotenv(os.path.join(os.getcwd(), 'backend/.env'))
django.setup()

from ai_services.llm import call_gemini

def test_gemini():
    print("Testing Gemini API with the new key...")
    prompt = "Hello Gemini! If you can read this, please reply with 'System Online' and a short greeting."
    
    try:
        response_text, usage = call_gemini(prompt, stream=False)
        if "Error" in response_text:
            print(f"❌ Gemini API Call Failed: {response_text}")
        else:
            print(f"✅ Gemini API Call Successful!")
            print(f"Response: {response_text}")
            print(f"Usage: {usage}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    test_gemini()
