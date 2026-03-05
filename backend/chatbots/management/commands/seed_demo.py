from django.core.management.base import BaseCommand
from accounts.models import User
from chatbots.models import Chatbot
from knowledge.models import KnowledgeFile, KnowledgeChunk
from conversations.models import Conversation, Message
from django.core.files.base import ContentFile
import random

class Command(BaseCommand):
    help = 'Seeds the database with demo data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding demo data...')

        # 1. Create Demo User
        user, created = User.objects.get_or_create(username='demo', defaults={'email': 'demo@example.com'})
        if created:
            user.set_password('demo123')
            user.save()
            self.stdout.write(self.style.SUCCESS('Created demo user'))
        else:
            self.stdout.write('Demo user already exists')

        # 2. Create Demo Chatbot
        chatbot, created = Chatbot.objects.get_or_create(
            name='Demo Bot',
            owner=user,
            defaults={
                'description': 'A demo chatbot for testing',
                'system_prompt': 'You are a friendly demo assistant.',
                'selected_llm': 'openai',
                'is_published': True,
                'is_active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created demo chatbot'))
        else:
            self.stdout.write('Demo chatbot already exists')

        # 3. Create Demo Knowledge
        if not KnowledgeFile.objects.filter(chatbot=chatbot).exists():
            k_file = KnowledgeFile.objects.create(
                chatbot=chatbot,
                status='ready'
            )
            # Use a dummy content file
            k_file.file.save('demo_knowledge.txt', ContentFile("This is some demo knowledge content."))
            self.stdout.write(self.style.SUCCESS('Created demo knowledge file'))

            # Create Chunks
            for i in range(3):
                # Generate a random embedding of size 1536
                embedding = [random.uniform(-0.1, 0.1) for _ in range(1536)]
                KnowledgeChunk.objects.create(
                    chatbot=chatbot,
                    knowledge_file=k_file,
                    content=f"This is demo chunk {i+1}. It contains important information about the demo.",
                    embedding=embedding
                )
            self.stdout.write(self.style.SUCCESS('Created 3 demo knowledge chunks'))
        else:
            self.stdout.write('Demo knowledge already exists')

        # 4. Create Demo Conversations
        if not Conversation.objects.filter(chatbot=chatbot).exists():
            conversation = Conversation.objects.create(
                chatbot=chatbot,
                visitor_identifier='demo_visitor_1'
            )
            
            Message.objects.create(
                conversation=conversation,
                sender='user',
                content='Hello, what can you do?'
            )
            Message.objects.create(
                conversation=conversation,
                sender='bot',
                content='I can help you with your demo queries!'
            )
            self.stdout.write(self.style.SUCCESS('Created demo conversation with messages'))
        else:
            self.stdout.write('Demo conversation already exists')

        self.stdout.write(self.style.SUCCESS('Successfully seeded demo data'))
