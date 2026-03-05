from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from chatbots.models import Chatbot
from conversations.models import Conversation, Message, Session, Visitor
from analytics.models import BotAnalyticsDaily
from rest_framework.test import APIClient
from django.urls import reverse

User = get_user_model()

class AnalyticsRealTimeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='analytics_user', password='password')
        self.chatbot = Chatbot.objects.create(owner=self.user, name='Analytics Bot')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.today = timezone.now().date()
        self.yesterday = self.today - timedelta(days=1)
        
        # 1. Create Historical Data (Yesterday)
        BotAnalyticsDaily.objects.create(
            chatbot=self.chatbot,
            date=self.yesterday,
            total_messages=10,
            active_sessions=5,
            avg_latency=100.0,
            total_tokens=1000,
            knowledge_hit_rate=50.0
        )
        
        # 2. Create Real-time Data (Today)
        # Create Visitor
        self.visitor = Visitor.objects.create(external_id='visitor1')
        
        # Create Session
        self.session = Session.objects.create(
            visitor=self.visitor,
            # start_time=timezone.now(), # auto_now_add handles this
            # last_activity=timezone.now() # auto_now handles this
        )
        
        # Create Conversation
        self.conversation = Conversation.objects.create(
            chatbot=self.chatbot, 
            visitor_identifier='visitor1',
            visitor=self.visitor,
            session=self.session,
            is_preview=False
        )
        
        # Messages (2 messages: 1 knowledge, 1 api)
        Message.objects.create(
            conversation=self.conversation,
            sender='bot',
            content='Msg 1',
            latency=50.0,
            token_usage=100,
            source='knowledge',
            created_at=timezone.now()
        )
        Message.objects.create(
            conversation=self.conversation,
            sender='bot',
            content='Msg 2',
            latency=150.0,
            token_usage=200,
            source='ai_api',
            created_at=timezone.now()
        )
        
        # Expected Today Stats:
        # Messages: 2
        # Sessions: 1
        # Latency: (50+150)/2 = 100.0
        # Tokens: 300
        # Hit Rate: 50%

    def test_analytics_overview_merges_data(self):
        url = reverse('analytics-overview', args=[self.chatbot.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Total Messages = 10 (Yesterday) + 2 (Today) = 12
        self.assertEqual(data['total_messages'], 12)
        
        # Total Sessions = 5 (Yesterday) + 1 (Today) = 6
        self.assertEqual(data['active_sessions'], 6)
        
        # Total Tokens = 1000 + 300 = 1300
        self.assertEqual(data['total_tokens'], 1300)
        
        # Avg Latency = ((100*1) + (100*1))/2 = 100 (Since we have 1 historical day and 1 today)
        self.assertEqual(data['avg_latency'], 100.0)

    def test_analytics_graph_merges_data(self):
        url = reverse('analytics-graph', args=[self.chatbot.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should have 2 entries (Yesterday and Today)
        # Note: Depending on how many days are in range. We only populated yesterday.
        # But loop iterates over existing records.
        # So we expect yesterday's record + today's appended record.
        
        self.assertTrue(len(data) >= 2)
        
        # Check Yesterday
        yesterday_str = self.yesterday.strftime('%Y-%m-%d')
        yesterday_data = next(d for d in data if d['date'] == yesterday_str)
        self.assertEqual(yesterday_data['messages'], 10)
        
        # Check Today
        today_str = self.today.strftime('%Y-%m-%d')
        today_data = next(d for d in data if d['date'] == today_str)
        self.assertEqual(today_data['messages'], 2)
        self.assertEqual(today_data['knowledge_hits'], 1)
        self.assertEqual(today_data['api_hits'], 1)
        self.assertEqual(today_data['knowledge_hit_rate'], 50.0)
