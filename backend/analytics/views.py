from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Count, Avg, Sum, Q
from django.db.models.functions import TruncDate, TruncHour
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
from chatbots.models import Chatbot
from conversations.models import Conversation, Message, Session
from .models import BotAnalyticsDaily, TokenUsage

class AnalyticsOverviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, chatbot_id):
        include_preview = request.query_params.get('include_preview', 'false').lower() == 'true'
        chatbot = get_object_or_404(Chatbot, id=chatbot_id, owner=request.user)
        
        today = timezone.now().date()
        start_date = today - timedelta(days=29)
        
        base_message_filter = Q(conversation__chatbot=chatbot, created_at__date=today)
        base_session_filter = Q(conversations__chatbot=chatbot, started_at__date=today)
        if not include_preview:
            base_message_filter &= Q(conversation__is_preview=False)
            base_session_filter &= Q(conversations__is_preview=False)

        historical_stats = BotAnalyticsDaily.objects.filter(
            chatbot=chatbot,
            date__range=[start_date, today - timedelta(days=1)]
        )
        
        hist_messages = historical_stats.aggregate(Sum('total_messages'))['total_messages__sum'] or 0
        hist_sessions = historical_stats.aggregate(Sum('active_sessions'))['active_sessions__sum'] or 0
        hist_tokens = historical_stats.aggregate(Sum('total_tokens'))['total_tokens__sum'] or 0
        hist_avg_latency = historical_stats.aggregate(Avg('avg_latency'))['avg_latency__avg'] or 0.0
        hist_avg_hit_rate = historical_stats.aggregate(Avg('knowledge_hit_rate'))['knowledge_hit_rate__avg'] or 0.0
        hist_count = historical_stats.count()

        today_messages_qs = Message.objects.filter(base_message_filter)
        today_msg_count = today_messages_qs.count()
        today_latency = today_messages_qs.aggregate(Avg('latency'))['latency__avg'] or 0.0
        
        today_sessions_count = Session.objects.filter(base_session_filter).distinct().count()
        today_tokens = today_messages_qs.aggregate(Sum('token_usage'))['token_usage__sum'] or 0
        
        today_knowledge_hits = today_messages_qs.filter(source='knowledge').count()
        today_hit_rate = (today_knowledge_hits / today_msg_count * 100) if today_msg_count > 0 else 0.0

        total_messages = hist_messages + today_msg_count
        active_sessions = hist_sessions + today_sessions_count
        total_tokens = hist_tokens + today_tokens
        
        total_days = hist_count + (1 if today_msg_count > 0 else 0)
        avg_latency = ((hist_avg_latency * hist_count) + (today_latency * (1 if today_msg_count > 0 else 0))) / total_days if total_days > 0 else 0
        avg_knowledge_hit_rate = ((hist_avg_hit_rate * hist_count) + (today_hit_rate * (1 if today_msg_count > 0 else 0))) / total_days if total_days > 0 else 0

        data = {
            "period": "last_30_days",
            "total_messages": total_messages,
            "active_sessions": active_sessions,
            "avg_latency": round(avg_latency, 2),
            "total_tokens": total_tokens,
            "knowledge_hit_rate": round(avg_knowledge_hit_rate, 2)
        }
        
        return Response(data)

class AnalyticsGraphView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, chatbot_id):
        include_preview = request.query_params.get('include_preview', 'false').lower() == 'true'
        chatbot = get_object_or_404(Chatbot, id=chatbot_id, owner=request.user)
        
        today = timezone.now().date()
        start_date = today - timedelta(days=29)
        
        daily_stats = BotAnalyticsDaily.objects.filter(
            chatbot=chatbot,
            date__range=[start_date, today - timedelta(days=1)]
        ).order_by('date')
        
        graph_data = []
        for stat in daily_stats:
            knowledge_hits = int(stat.total_messages * (stat.knowledge_hit_rate / 100))
            api_hits = stat.total_messages - knowledge_hits
            
            graph_data.append({
                "date": stat.date.strftime('%Y-%m-%d'),
                "messages": stat.total_messages,
                "sessions": stat.active_sessions,
                "latency": stat.avg_latency,
                "tokens": stat.total_tokens,
                "knowledge_hits": knowledge_hits,
                "api_hits": api_hits,
                "knowledge_hit_rate": stat.knowledge_hit_rate
            })

        base_message_filter = Q(conversation__chatbot=chatbot, created_at__date=today)
        base_session_filter = Q(conversations__chatbot=chatbot, started_at__date=today)
        if not include_preview:
            base_message_filter &= Q(conversation__is_preview=False)
            base_session_filter &= Q(conversations__is_preview=False)

        today_messages_qs = Message.objects.filter(base_message_filter)
        today_msg_count = today_messages_qs.count()
        today_sessions_count = Session.objects.filter(base_session_filter).distinct().count()
        today_latency = today_messages_qs.aggregate(Avg('latency'))['latency__avg'] or 0.0
        today_tokens = today_messages_qs.aggregate(Sum('token_usage'))['token_usage__sum'] or 0
        today_knowledge_hits = today_messages_qs.filter(source='knowledge').count()
        today_api_hits = today_messages_qs.filter(source='ai_api').count()
        today_hit_rate = (today_knowledge_hits / today_msg_count * 100) if today_msg_count > 0 else 0.0

        graph_data.append({
            "date": today.strftime('%Y-%m-%d'),
            "messages": today_msg_count,
            "sessions": today_sessions_count,
            "latency": round(today_latency, 2),
            "tokens": today_tokens,
            "knowledge_hits": today_knowledge_hits,
            "api_hits": today_api_hits,
            "knowledge_hit_rate": round(today_hit_rate, 2)
        })
        
        return Response(graph_data)

class AnalyticsLiveView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, chatbot_id):
        include_preview = request.query_params.get('include_preview', 'false').lower() == 'true'
        chatbot = get_object_or_404(Chatbot, id=chatbot_id, owner=request.user)
        
        now = timezone.now()
        last_5_minutes = now - timedelta(minutes=5)
        last_hour = now - timedelta(hours=1)
        
        session_filter = Q(conversations__chatbot=chatbot, last_activity__gte=last_5_minutes)
        message_filter = Q(conversation__chatbot=chatbot, created_at__gte=last_hour)
        if not include_preview:
            session_filter &= Q(conversations__is_preview=False)
            message_filter &= Q(conversation__is_preview=False)

        active_sessions_5m = Session.objects.filter(session_filter).distinct().count()
        messages_1h = Message.objects.filter(message_filter).count()
        
        avg_latency_1h = Message.objects.filter(message_filter, sender='bot').aggregate(Avg('latency'))['latency__avg'] or 0.0

        data = {
            "active_sessions_5m": active_sessions_5m,
            "messages_1h": messages_1h,
            "avg_latency_1h": round(avg_latency_1h, 2)
        }
        
        return Response(data)

class AnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, chatbot_id):
        # Ensure the chatbot exists and belongs to the authenticated user
        chatbot = get_object_or_404(Chatbot, id=chatbot_id, owner=request.user)

        # 1. Total conversations count - Exclude preview
        total_conversations = Conversation.objects.filter(chatbot=chatbot, is_preview=False).count()

        # 2. Total messages count - Exclude preview
        total_messages = Message.objects.filter(conversation__chatbot=chatbot, conversation__is_preview=False).count()

        # 3. Unique visitor count - Exclude preview
        unique_visitors = Conversation.objects.filter(chatbot=chatbot, is_preview=False).values('visitor_id').distinct().count()

        # 4. Daily message aggregation - Exclude preview
        daily_messages = (
            Message.objects.filter(conversation__chatbot=chatbot, conversation__is_preview=False)
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )

        return Response({
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "unique_visitors": unique_visitors,
            "daily_messages": list(daily_messages)
        })
