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
    if context:
        base_system = (
            "You are a business AI assistant.\n"
            "Answer using provided context.\n"
            "If answer not found say you don't know."
        )
        parts.append(f"System:\n{base_system}")
    else:
        # Fallback to general AI provider (General Knowledge)
        if fallback_behavior:
            base_system = fallback_behavior
        else:
            base_system = (
                "You are a business AI assistant.\n"
                "Answer the user's question helpfully and accurately using your general knowledge."
            )
        parts.append(f"System:\n{base_system}")
    
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
