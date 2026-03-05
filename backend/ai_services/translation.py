import json
from .llm import call_gemini, call_openai
from monitoring.utils import Logger

class TranslationService:
    @staticmethod
    def detect_and_translate(text, chatbot):
        """
        Detects the language of the text and translates it to English if necessary.
        Returns a tuple: (original_language, translated_text)
        """
        prompt = (
            "You are a translation engine. Detect the language of the following text and translate it to English. "
            "If it is already in English, return it exactly as is. "
            "Return ONLY a JSON object with keys 'language' and 'translated_text'.\n\n"
            f"Text: {text}"
        )
        
        try:
            if chatbot.selected_llm == 'gemini':
                response, _ = call_gemini(prompt)
            else:
                response, _ = call_openai(prompt)
            
            # Clean response to ensure valid JSON (remove markdown fences if any)
            cleaned_response = response.strip().replace('```json', '').replace('```', '')
            data = json.loads(cleaned_response)
            
            return data.get('language', 'English'), data.get('translated_text', text)
            
        except Exception as e:
            Logger.error('TRANSLATION', f"Input translation failed: {e}")
            # Fallback: assume English or return original
            return 'English', text

    @staticmethod
    def translate_response(text, target_language, chatbot):
        """
        Translates the text to the target language.
        """
        if not target_language or target_language.lower() == 'english':
            return text
            
        prompt = (
            f"Translate the following text to {target_language}. "
            "Maintain the original tone and formatting. "
            "Return ONLY the translated text.\n\n"
            f"Text: {text}"
        )
        
        try:
            if chatbot.selected_llm == 'gemini':
                response, _ = call_gemini(prompt)
            else:
                response, _ = call_openai(prompt)
            
            return response.strip()
            
        except Exception as e:
            Logger.error('TRANSLATION', f"Output translation failed: {e}")
            return text
