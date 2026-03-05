import os
from openai import OpenAI
import google.generativeai as genai
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
    Returns:
        - If stream=False: (response_text, usage_dict)
        - If stream=True: generator
    """
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or 'placeholder' in api_key:
        msg = "Gemini API key is missing."
        Logger.error('AI', msg)
        return f"Error: {msg}", {}

    try:
        genai.configure(api_key=api_key)
        # using gemini-flash-latest model as it is free tier eligible
        model = genai.GenerativeModel('gemini-flash-latest')
        response = model.generate_content(prompt, stream=stream)
        if stream:
            return response
        else:
            # Gemini usage_metadata
            # structure: prompt_token_count, candidates_token_count, total_token_count
            usage = {}
            if hasattr(response, 'usage_metadata'):
                usage = {
                    'prompt_tokens': response.usage_metadata.prompt_token_count,
                    'completion_tokens': response.usage_metadata.candidates_token_count,
                    'total_tokens': response.usage_metadata.total_token_count
                }
            return response.text, usage
    except Exception as e:
        Logger.error('AI', f"Gemini Call Failed: {e}", {'stream': stream})
        return f"Error calling Gemini: {e}", {}
