from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from chatbots.models import Chatbot
from conversations.models import Conversation, Message, Session, Visitor

@override_settings(CACHES={
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
})
class ConversationHistoryTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='password')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.chatbot = Chatbot.objects.create(name="Test Bot", owner=self.user)
        self.visitor = Visitor.objects.create(external_id="visitor1")
        self.session = Session.objects.create(visitor=self.visitor)
        self.conversation = Conversation.objects.create(
            chatbot=self.chatbot,
            visitor=self.visitor,
            session=self.session,
            visitor_identifier="visitor1"
        )
        self.message = Message.objects.create(
            conversation=self.conversation,
            sender='user',
            content='Hello'
        )

    def test_list_conversations(self):
        response = self.client.get('/api/history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if response.data is list or dict with results (pagination)
        results = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['visitor_identifier'], 'visitor1')

    def test_filter_by_bot(self):
        response = self.client.get(f'/api/history/?chatbot_id={self.chatbot.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(results), 1)
        
        response = self.client.get(f'/api/history/?chatbot_id={self.chatbot.id + 1}')
        results_empty = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(results_empty), 0)

    def test_retrieve_conversation(self):
        response = self.client.get(f'/api/history/{self.conversation.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['messages']), 1)
        self.assertEqual(response.data['messages'][0]['content'], 'Hello')
