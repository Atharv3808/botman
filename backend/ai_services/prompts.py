def build_rag_prompt(chatbot, context, history, question):
    """
    Constructs the central prompt template for RAG-based chat.
    
    Structure:
    1. Base System Instruction / Fallback
    2. Personality
    3. Chatbot Instructions (System Prompt)
    4. Guardrails
    5. Knowledge Context
    6. Conversation History
    7. User Question
    """
    prompt_config = getattr(chatbot, 'bot_prompt_config', {}) or {}
    
    # Prioritize model fields, fallback to config for backward compat
    personality = getattr(chatbot, 'personality', '') or prompt_config.get('personality', '')
    tone = getattr(chatbot, 'tone', '')
    guardrails = prompt_config.get('guardrails', '')
    fallback_behavior = getattr(chatbot, 'fallback_behavior', '') or prompt_config.get('fallback_prompt', '')
    system_prompt = chatbot.system_prompt or prompt_config.get('system_prompt', '')
    
    parts = []

    # 1. Base System Instruction / Fallback
    formatting_config = getattr(chatbot, 'formatting_config', {}) or {}
    use_markdown = formatting_config.get('use_markdown', True)
    use_code_blocks = formatting_config.get('use_code_blocks', True)
    use_tables = formatting_config.get('use_tables', True)
    
    formatting_parts = []
    if use_markdown:
        formatting_parts.append("Format your response using proper Markdown.")
        formatting_parts.append("Use headers (##) for sections.")
        formatting_parts.append("Use bullet points for lists.")
    if use_code_blocks:
        formatting_parts.append("Use code blocks with language tags for snippets (e.g., ```python).")
    if use_tables:
        formatting_parts.append("Use markdown tables for structured data when applicable.")
    
    formatting_instruction = ""
    if formatting_parts:
        formatting_instruction = "\nIMPORTANT: " + " ".join(formatting_parts) + " Keep paragraphs short and use bold text for key terms."
    
    if context:
        base_system = (
            "You are a business AI assistant.\n"
            "Answer using provided context.\n"
            "If answer not found say you don't know."
        )
        parts.append(f"System:\n{base_system}{formatting_instruction}")
    else:
        # Fallback to general AI provider (General Knowledge)
        if fallback_behavior:
            base_system = fallback_behavior
        else:
            base_system = (
                "You are a business AI assistant.\n"
                "Answer the user's question helpfully and accurately using your general knowledge."
            )
        parts.append(f"System:\n{base_system}{formatting_instruction}")
    
    # 2. Personality & Tone
    if personality:
        parts.append(f"Personality:\n{personality}")
    if tone:
        parts.append(f"Tone:\n{tone}")

    # 3. Chatbot Specific Instructions
    if system_prompt:
        parts.append(f"Chatbot Instructions:\n{system_prompt}")
    
    # 4. Guardrails
    if guardrails:
        parts.append(f"Guardrails:\n{guardrails}")
    
    # 5. Knowledge Context
    if context:
        parts.append(f"Context Information:\n{context}")
    
    # 6. Conversation History
    if history:
        parts.append(f"Conversation History:\n{history}")
    
    # 7. User Question
    parts.append(f"User Question: {question}")
    
    return "\n\n".join(parts)
