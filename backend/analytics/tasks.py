from celery import shared_task
from django.utils import timezone
from django.db.models import Count, Avg, Sum
from datetime import timedelta
from chatbots.models import Chatbot
from conversations.models import Message, Session
from .models import BotAnalyticsDaily

@shared_task
def aggregate_daily_analytics(date_str=None):
    """
    Aggregates analytics for a specific date (default: yesterday).
    date_str format: 'YYYY-MM-DD'
    """
    if date_str:
        target_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        # Default to yesterday as we want to aggregate full day's data
        target_date = timezone.now().date() - timedelta(days=1)
        
    print(f"Aggregating analytics for {target_date}")

    for chatbot in Chatbot.objects.all():
        # 1. Daily Messages (Exclude preview)
        daily_messages = Message.objects.filter(
            conversation__chatbot=chatbot,
            conversation__is_preview=False,
            created_at__date=target_date
        )
        total_messages = daily_messages.count()
        
        if total_messages == 0:
            BotAnalyticsDaily.objects.update_or_create(
                chatbot=chatbot,
                date=target_date,
                defaults={
                    'total_messages': 0,
                    'active_sessions': 0,
                    'avg_latency': 0.0,
                    'total_tokens': 0,
                    'knowledge_hit_rate': 0.0
                }
            )
            continue

        # 2. Active Sessions
        # Count sessions that had any message on this day
        active_sessions = Session.objects.filter(
            conversations__messages__in=daily_messages
        ).distinct().count()

        # 3. Avg Response Time (Latency) - only for bot messages
        bot_messages = daily_messages.filter(sender='bot')
        avg_latency = bot_messages.aggregate(Avg('latency'))['latency__avg'] or 0.0

        # 4. AI Usage (Total Tokens)
        total_tokens = daily_messages.aggregate(Sum('token_usage'))['token_usage__sum'] or 0

        # 5. Knowledge Hit Rate
        # Messages with source='knowledge' / Total bot messages
        knowledge_messages = bot_messages.filter(source='knowledge').count()
        total_bot_messages = bot_messages.count()
        
        knowledge_hit_rate = 0.0
        if total_bot_messages > 0:
            knowledge_hit_rate = (knowledge_messages / total_bot_messages) * 100

        # Store
        BotAnalyticsDaily.objects.update_or_create(
            chatbot=chatbot,
            date=target_date,
            defaults={
                'total_messages': total_messages,
                'active_sessions': active_sessions,
                'avg_latency': avg_latency,
                'total_tokens': total_tokens,
                'knowledge_hit_rate': knowledge_hit_rate
            }
        )
    
    return f"Aggregated analytics for {target_date}"
