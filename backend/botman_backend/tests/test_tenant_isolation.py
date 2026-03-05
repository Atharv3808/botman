from django.test import TestCase
from django.contrib.auth import get_user_model
from chatbots.models import Chatbot
from conversations.models import Conversation
from botman_backend.tenant_context import tenant_context

User = get_user_model()

class TenantIsolationTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username='user_a', password='password')
        self.user_b = User.objects.create_user(username='user_b', password='password')
        
        self.bot_a = Chatbot.objects.create(name='Bot A', owner=self.user_a)
        self.bot_b = Chatbot.objects.create(name='Bot B', owner=self.user_b)
        
        self.convo_a = Conversation.objects.create(chatbot=self.bot_a, visitor_identifier='v1')
        self.convo_b = Conversation.objects.create(chatbot=self.bot_b, visitor_identifier='v2')

    def test_chatbot_isolation_by_user(self):
        # No context -> All objects (default behavior for non-context calls)
        with tenant_context(user_id=None):
             self.assertEqual(Chatbot.objects.count(), 2)

        # User A context -> Only Bot A
        with tenant_context(user_id=self.user_a.id):
            self.assertEqual(Chatbot.objects.count(), 1)
            self.assertEqual(Chatbot.objects.first(), self.bot_a)
            
        # User B context -> Only Bot B
        with tenant_context(user_id=self.user_b.id):
            self.assertEqual(Chatbot.objects.count(), 1)
            self.assertEqual(Chatbot.objects.first(), self.bot_b)

    def test_conversation_isolation_by_user(self):
        # User A context -> Only Conversation A
        with tenant_context(user_id=self.user_a.id):
            self.assertEqual(Conversation.objects.count(), 1)
            self.assertEqual(Conversation.objects.first(), self.convo_a)

    def test_isolation_by_bot_id(self):
        # User A context + Bot A context -> Bot A found
        with tenant_context(user_id=self.user_a.id, bot_id=self.bot_a.id):
            self.assertEqual(Chatbot.objects.count(), 1)
            self.assertEqual(Chatbot.objects.first(), self.bot_a)
            
        # User A context + Bot B context -> Empty (User A doesn't own Bot B)
        with tenant_context(user_id=self.user_a.id, bot_id=self.bot_b.id):
            self.assertEqual(Chatbot.objects.count(), 0)

    def test_superuser_access(self):
        superuser = User.objects.create_superuser(username='admin', password='password')
        with tenant_context(user_id=superuser.id, is_superuser=True):
            self.assertEqual(Chatbot.objects.count(), 2)
