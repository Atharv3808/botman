from conversations.models import Message

class ContextBuilderService:
    @staticmethod
    def get_conversation_history(conversation, limit=10, exclude_message_id=None):
        """
        Retrieves and formats the recent conversation history for multi-turn context.
        Fetches the last `limit` messages (default 10) to support natural conversation flow.
        
        Args:
            conversation (Conversation): The conversation object.
            limit (int): Number of recent messages to retrieve.
            exclude_message_id (int): ID of a message to exclude (e.g., the current user message if already saved).
            
        Returns:
            str: Formatted conversation history string (User: ... \nAssistant: ...).
        """
        query = Message.objects.filter(conversation=conversation)
        
        if exclude_message_id:
            query = query.exclude(id=exclude_message_id)
            
        # Fetch last N messages
        recent_messages = query.order_by('-created_at')[:limit]
        
        history_text = ""
        # Reverse to chronological order (Oldest -> Newest)
        for msg in reversed(list(recent_messages)):
            role = "User" if msg.sender == 'user' else "Assistant"
            history_text += f"{role}: {msg.content}\n"
            
        return history_text
