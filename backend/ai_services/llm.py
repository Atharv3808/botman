import os
import backoff
from openai import OpenAI
from google import genai
from google.genai import errors
from monitoring.utils import Logger

def call_openai(prompt, model="gpt-3.5-turbo", stream=False):
    """
    Calls OpenAI API to generate a response.
    Returns:
        - If stream=False: (response_text, usage_dict)
        - If stream=True: generator yielding chunks, with usage as last item
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or 'placeholder' in api_key:
        msg = "OpenAI API key is missing."
        Logger.error('AI', msg)
        return f"Error: {msg}", {}

    client = OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            stream=stream,
            stream_options={"include_usage": True} if stream else None
        )
        if stream:
            return response
        else:
            usage = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
            return response.choices[0].message.content, usage
    except Exception as e:
        Logger.error('AI', f"OpenAI Call Failed: {e}", {'model': model, 'stream': stream})
        return f"Error calling OpenAI: {e}", {}

def call_gemini(prompt, stream=False):
    """
    Calls Google Gemini API to generate a response.
    Includes exponential backoff for rate limits.
    """
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or 'placeholder' in api_key:
        msg = "Gemini API key is missing."
        Logger.error('AI', msg)
        return f"Error: {msg}", {}

    try:
        client = genai.Client(api_key=api_key)
        # Use models/gemini-flash-latest as seen in the model list
        model_id = 'models/gemini-flash-latest'
        
        @backoff.on_exception(
            backoff.expo,
            (errors.ClientError),
            max_tries=3,
            giveup=lambda e: getattr(e, 'code', None) != 429
        )
        def _execute_call(m_id):
            if stream:
                return client.models.generate_content_stream(model=m_id, contents=prompt)
            else:
                return client.models.generate_content(model=m_id, contents=prompt)

        response = _execute_call(model_id)
        
        if stream:
            return response
        else:
            # Safely extract text
            try:
                response_text = response.text
            except Exception:
                response_text = "I'm sorry, I cannot generate a response to that prompt due to safety filters or an empty response."

            # Gemini usage_metadata
            usage = {}
            if hasattr(response, 'usage_metadata'):
                usage = {
                    'prompt_tokens': response.usage_metadata.prompt_token_count,
                    'completion_tokens': response.usage_metadata.candidates_token_count,
                    'total_tokens': response.usage_metadata.total_token_count
                }
            return response_text, usage

    except errors.ClientError as e:
        if getattr(e, 'code', None) == 429:
            # If gemini-flash-latest is exhausted, try 2.0-flash as a fallback
            try:
                Logger.warning('AI', "Gemini flash-latest quota exhausted, trying 2.0-flash fallback")
                model_id = 'models/gemini-2.0-flash'
                response = _execute_call(model_id)
                if stream: return response
                usage = {}
                if hasattr(response, 'usage_metadata'):
                    usage = {
                        'prompt_tokens': response.usage_metadata.prompt_token_count,
                        'completion_tokens': response.usage_metadata.candidates_token_count,
                        'total_tokens': response.usage_metadata.total_token_count
                    }
                return response.text, usage
            except Exception as fallback_err:
                Logger.error('AI', f"Gemini Fallback Failed: {fallback_err}")
                return "The AI service is currently overloaded (Rate Limit Exceeded). Please try again in a moment.", {}
        
        Logger.error('AI', f"Gemini Call Failed: {e}", {'stream': stream})
        return f"Error calling Gemini: {e}", {}
    except Exception as e:
        Logger.error('AI', f"Gemini Call Failed: {e}", {'stream': stream})
        return f"Error calling Gemini: {e}", {}
