from .models import Conversation, Message, Visitor
from ai_services.utils import embed_text, search_knowledge
from ai_services.llm import call_openai, call_gemini
from ai_services.prompts import build_rag_prompt
from ai_services.context_builder import ContextBuilderService
from ai_services.translation import TranslationService
from monitoring.utils import Logger
import time
import json

def process_chat_message(chatbot, visitor_id, message_text, stream=True, preview_mode=False):
    """
    Processes a chat message through the RAG pipeline.
    Returns the response text and conversation object.
    If stream=True, returns a generator that yields chunks.
    """
    start_time = time.time()
    
    # Log widget usage
    if not preview_mode:
        Logger.info('WIDGET', f"Processing message for Bot {chatbot.name}", {
            'bot_id': chatbot.id,
            'visitor_id': visitor_id,
            'length': len(message_text)
        })

    # Apply runtime config if not in preview mode
    if not preview_mode:
        config = chatbot.get_runtime_config()
        # Override attributes in memory
        chatbot.system_prompt = config.get('system_prompt', chatbot.system_prompt)
        chatbot.selected_llm = config.get('selected_llm', chatbot.selected_llm)
        chatbot.bot_prompt_config = config.get('bot_prompt_config', getattr(chatbot, 'bot_prompt_config', {}))

    # Detect and translate language (step 1)
    original_language, translated_message_text = TranslationService.detect_and_translate(message_text, chatbot)
    if original_language.lower() != 'english':
        Logger.info('TRANSLATION', f"Detected {original_language}. Translated: '{message_text}' -> '{translated_message_text}'")
        # Use translated text for processing
        processing_text = translated_message_text
    else:
        processing_text = message_text

    # Get or create Visitor
    visitor, _ = Visitor.objects.get_or_create(external_id=visitor_id)

    # Get or create conversation
    conversation, created = Conversation.objects.get_or_create(
        chatbot=chatbot,
        visitor_identifier=visitor_id,
        defaults={'visitor': visitor, 'is_preview': preview_mode}
    )
    
    # Update is_preview if existing conversation (though usually visitor_id for preview should be unique/session-based)
    if not created and conversation.is_preview != preview_mode:
        conversation.is_preview = preview_mode
        conversation.save()
    
    # Ensure visitor is linked (for migration/compatibility)
    if not conversation.visitor:
        conversation.visitor = visitor
        conversation.save()
    
    # Save user message
    user_message = Message.objects.create(
        conversation=conversation,
        sender='user',
        content=message_text
    )
    
    # Retrieve conversation history using ContextBuilderService
    # Limit set to 10 to support multi-turn logic and natural conversations
    history_text = ContextBuilderService.get_conversation_history(
        conversation=conversation,
        limit=10,
        exclude_message_id=user_message.id
    )
    
    # Embed message (use translated text)
    embedding = embed_text(processing_text)
    
    # Search knowledge (use translated text for both embedding and keyword search)
    # Default parameters: limit=3, threshold=0.7 (can be made configurable per chatbot later)
    context = ""
    source = "ai_api"
    confidence_score = 0.0
    
    if embedding:
        chunks = search_knowledge(chatbot, embedding, query_text=processing_text, limit=3, threshold=0.7)
        if chunks:
            # Calculate confidence score from the best match (first chunk)
            # Similarity = 1 - Distance
            if hasattr(chunks[0], 'distance'):
                confidence_score = max(0.0, 1.0 - chunks[0].distance)
            elif hasattr(chunks[0], 'combined_score'): # Hybrid search score
                confidence_score = chunks[0].combined_score
            
            context_texts = [chunk.content for chunk in chunks]
            context = "\n\n".join(context_texts)
            source = "knowledge"
    
    # Construct prompt (use translated text)
    prompt = build_rag_prompt(
        chatbot=chatbot,
        context=context,
        history=history_text,
        question=processing_text
    )
        
    # Call LLM
    if stream and original_language.lower() == 'english':
        # If English, stream normally
        return stream_response_generator(chatbot, prompt, conversation, start_time=start_time, source=source, confidence_score=confidence_score, preview_mode=preview_mode)
    else:
        # If non-English or stream=False, block and translate if needed
        response_text = ""
        usage = {}
        if chatbot.selected_llm == 'gemini':
            response_text, usage = call_gemini(prompt)
        else:
            # Default to OpenAI
            response_text, usage = call_openai(prompt)
            
        # Translate response back if needed
        if original_language.lower() != 'english':
            response_text = TranslationService.translate_response(response_text, original_language, chatbot)
            
        latency = (time.time() - start_time) * 1000
            
        # Save bot response
        Message.objects.create(
            conversation=conversation,
            sender='bot',
            content=response_text,
            latency=latency,
            token_usage=usage.get('total_tokens', 0),
            source=source,
            confidence_score=confidence_score
        )
        
        # Save token usage if not in preview mode (Legacy Analytics)
        if usage and not preview_mode:
            try:
                from analytics.models import TokenUsage
                TokenUsage.objects.create(
                    chatbot=chatbot,
                    provider=chatbot.selected_llm,
                    tokens_input=usage.get('prompt_tokens', 0),
                    tokens_output=usage.get('completion_tokens', 0),
                    total_tokens=usage.get('total_tokens', 0)
                )
            except Exception as e:
                print(f"Error saving token usage: {e}")
        
        if stream:
             # Simulate stream for non-English users (yield single chunk)
             def simple_generator():
                 yield f"data: {json.dumps({'content': response_text})}\n\n"
             return simple_generator()
        
        return response_text, conversation

def stream_response_generator(chatbot, prompt, conversation, start_time=None, source="ai_api", confidence_score=0.0, preview_mode=False):
    """
    Generator wrapper for streaming responses.
    Accumulates the full response and saves it to DB on completion.
    Also tracks token usage.
    """
    if start_time is None:
        start_time = time.time()
        
    full_response = ""
    usage = {}
    
    if chatbot.selected_llm == 'gemini':
        response_stream = call_gemini(prompt, stream=True)
        # Gemini stream returns chunks with .text
        if isinstance(response_stream, str): # Handle error case
             yield f"event: error\ndata: {json.dumps({'message': response_stream})}\n\n"
             full_response = response_stream
        else:
            try:
                for chunk in response_stream:
                    chunk_text = chunk.text
                    full_response += chunk_text
                    yield f"data: {json.dumps({'content': chunk_text})}\n\n"
                
                # Gemini usage metadata is in the last response object, but iterating consumes it.
                # Actually, in google-generativeai, usage_metadata is available on the response object after iteration
                # if we have access to it. But here response_stream is the GenerateContentResponse (iterable).
                # Let's try to access usage_metadata from response_stream after iteration.
                if hasattr(response_stream, 'usage_metadata'):
                     usage = {
                        'prompt_tokens': response_stream.usage_metadata.prompt_token_count,
                        'completion_tokens': response_stream.usage_metadata.candidates_token_count,
                        'total_tokens': response_stream.usage_metadata.total_token_count
                    }
            except Exception as e:
                error_msg = f"Error streaming from Gemini: {e}"
                yield f"event: error\ndata: {json.dumps({'message': error_msg})}\n\n"
                full_response += error_msg
    else:
        # OpenAI stream
        response_stream = call_openai(prompt, stream=True)
        if isinstance(response_stream, str): # Handle error case
            yield f"event: error\ndata: {json.dumps({'message': response_stream})}\n\n"
            full_response = response_stream
        else:
            try:
                for chunk in response_stream:
                    if chunk.choices and chunk.choices[0].delta.content is not None:
                        chunk_text = chunk.choices[0].delta.content
                        full_response += chunk_text
                        yield f"data: {json.dumps({'content': chunk_text})}\n\n"
                    
                    # Check for usage in the last chunk (stream_options={"include_usage": True})
                    if hasattr(chunk, 'usage') and chunk.usage:
                        usage = {
                            'prompt_tokens': chunk.usage.prompt_tokens,
                            'completion_tokens': chunk.usage.completion_tokens,
                            'total_tokens': chunk.usage.total_tokens
                        }
            except Exception as e:
                error_msg = f"Error streaming from OpenAI: {e}"
                yield f"event: error\ndata: {json.dumps({'message': error_msg})}\n\n"
                full_response += error_msg
                
    latency = (time.time() - start_time) * 1000

    # Save complete message to DB
    Message.objects.create(
        conversation=conversation,
        sender='bot',
        content=full_response,
        latency=latency,
        token_usage=usage.get('total_tokens', 0),
        source=source,
        confidence_score=confidence_score
    )
    
    # Save token usage if not in preview mode
    if usage and not preview_mode:
        try:
            from analytics.models import TokenUsage
            TokenUsage.objects.create(
                chatbot=chatbot,
                provider=chatbot.selected_llm,
                tokens_input=usage.get('prompt_tokens', 0),
                tokens_output=usage.get('completion_tokens', 0),
                total_tokens=usage.get('total_tokens', 0)
            )
        except Exception as e:
            print(f"Error saving token usage: {e}")
