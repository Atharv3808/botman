from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
from chatbots.models import Chatbot
from conversations.models import Conversation, Message, Session, Visitor
from analytics.models import BotAnalyticsDaily
from analytics.tasks import aggregate_daily_analytics

class AnalyticsTaskTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='testuser', password='password')
        
        # Create Chatbot
        self.chatbot = Chatbot.objects.create(
            name="Test Bot",
            system_prompt="You are a test bot.",
            owner=self.user
        )
        
        # Create Visitor
        self.visitor = Visitor.objects.create(external_id="visitor_1")
        
        # Create Session
        self.session = Session.objects.create(visitor=self.visitor)
        
        # Create Conversation
        self.conversation = Conversation.objects.create(
            chatbot=self.chatbot,
            visitor_identifier="visitor_1",
            visitor=self.visitor,
            session=self.session
        )
        
        # Set target date to yesterday
        self.target_date = timezone.now().date() - timedelta(days=1)
        self.target_date_str = self.target_date.strftime('%Y-%m-%d')
        
        # Create Messages for yesterday
        # Message 1: User
        msg1 = Message.objects.create(
            conversation=self.conversation,
            sender='user',
            content='Hello',
            token_usage=0
        )
        msg1.created_at = timezone.now() - timedelta(days=1)
        msg1.save()
        
        # Message 2: Bot (Knowledge)
        msg2 = Message.objects.create(
            conversation=self.conversation,
            sender='bot',
            content='Hi from knowledge',
            latency=100.0,
            token_usage=50,
            source='knowledge'
        )
        msg2.created_at = timezone.now() - timedelta(days=1)
        msg2.save()
        
        # Message 3: Bot (AI API)
        msg3 = Message.objects.create(
            conversation=self.conversation,
            sender='bot',
            content='Hi from AI',
            latency=200.0,
            token_usage=50,
            source='ai_api'
        )
        msg3.created_at = timezone.now() - timedelta(days=1)
        msg3.save()
        
    def test_aggregate_daily_analytics(self):
        # Run task
        aggregate_daily_analytics(date_str=self.target_date_str)
        
        # Verify
        analytics = BotAnalyticsDaily.objects.get(chatbot=self.chatbot, date=self.target_date)
        
        self.assertEqual(analytics.total_messages, 3)
        self.assertEqual(analytics.active_sessions, 1)
        self.assertEqual(analytics.avg_latency, 150.0) # (100 + 200) / 2
        self.assertEqual(analytics.total_tokens, 100) # 0 + 50 + 50
        self.assertEqual(analytics.knowledge_hit_rate, 50.0) # 1 knowledge / 2 bot messages * 100
        
    def test_aggregate_daily_analytics_no_data(self):
        # Run task for today (no data)
        today_str = timezone.now().date().strftime('%Y-%m-%d')
        aggregate_daily_analytics(date_str=today_str)
        
        analytics = BotAnalyticsDaily.objects.get(chatbot=self.chatbot, date=timezone.now().date())
        
        self.assertEqual(analytics.total_messages, 0)
        self.assertEqual(analytics.active_sessions, 0)
        self.assertEqual(analytics.avg_latency, 0.0)
        self.assertEqual(analytics.total_tokens, 0)
        self.assertEqual(analytics.knowledge_hit_rate, 0.0)

class AnalyticsAPITest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create Chatbot
        self.chatbot = Chatbot.objects.create(
            name="Test Bot",
            system_prompt="You are a test bot.",
            owner=self.user
        )
        
        # Create some historical data
        self.target_date = timezone.now().date() - timedelta(days=1)
        BotAnalyticsDaily.objects.create(
            chatbot=self.chatbot,
            date=self.target_date,
            total_messages=10,
            active_sessions=5,
            avg_latency=200.0,
            total_tokens=500,
            knowledge_hit_rate=60.0
        )

    def test_analytics_overview(self):
        url = reverse('analytics-overview', kwargs={'chatbot_id': self.chatbot.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_messages'], 10)
        self.assertEqual(response.data['active_sessions'], 5)
        self.assertEqual(response.data['avg_latency'], 200.0)
        self.assertEqual(response.data['total_tokens'], 500)
        self.assertEqual(response.data['knowledge_hit_rate'], 60.0)

    def test_analytics_graph(self):
        url = reverse('analytics-graph', kwargs={'chatbot_id': self.chatbot.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['date'], self.target_date.strftime('%Y-%m-%d'))
        self.assertEqual(response.data[0]['messages'], 10)
        self.assertEqual(response.data[0]['knowledge_hit_rate'], 60.0)
        self.assertEqual(response.data[0]['knowledge_hits'], 6)
        self.assertEqual(response.data[0]['api_hits'], 4)

    def test_analytics_live(self):
        # Create live data
        visitor = Visitor.objects.create(external_id="live_visitor")
        session = Session.objects.create(visitor=visitor)
        conversation = Conversation.objects.create(chatbot=self.chatbot, visitor=visitor, session=session, visitor_identifier="live_visitor")
        
        Message.objects.create(
            conversation=conversation,
            sender='bot',
            content='Live message',
            latency=150.0
        )
        
        url = reverse('analytics-live', kwargs={'chatbot_id': self.chatbot.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['messages_1h'], 1)
        self.assertEqual(response.data['avg_latency_1h'], 150.0)
        self.assertEqual(response.data['active_sessions_5m'], 1)
