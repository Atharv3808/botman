from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from chatbots.models import Chatbot
from knowledge.models import KnowledgeFile, KnowledgeChunk
import os
import shutil
from django.conf import settings

User = get_user_model()

class DeletionTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.chatbot = Chatbot.objects.create(owner=self.user, name='Test Bot')
        
        # Create a dummy file
        self.file_content = b"This is a test file."
        self.file_name = "test_file_deletion.txt"
        self.file = SimpleUploadedFile(self.file_name, self.file_content)
        self.knowledge_file = KnowledgeFile.objects.create(chatbot=self.chatbot, file=self.file)
        
        # Create a chunk
        self.chunk = KnowledgeChunk.objects.create(
            chatbot=self.chatbot, 
            knowledge_file=self.knowledge_file, 
            content="Chunk content"
        )

    def tearDown(self):
        # Cleanup any remaining files if test failed
        if self.knowledge_file.pk and KnowledgeFile.objects.filter(pk=self.knowledge_file.pk).exists():
             if self.knowledge_file.file and os.path.exists(self.knowledge_file.file.path):
                os.remove(self.knowledge_file.file.path)

    def test_delete_knowledge_file_cleans_up_file(self):
        file_path = self.knowledge_file.file.path
        self.assertTrue(os.path.exists(file_path), "File should exist on disk after creation")
        
        # Delete the knowledge file
        self.knowledge_file.delete()
        
        # Verify DB deletion
        self.assertFalse(KnowledgeFile.objects.filter(pk=self.knowledge_file.pk).exists())
        self.assertFalse(KnowledgeChunk.objects.filter(pk=self.chunk.pk).exists())
        
        # Verify file deletion (Signal check)
        self.assertFalse(os.path.exists(file_path), "File should be deleted from disk after object deletion")

    def test_delete_chatbot_cascades_and_cleans_up(self):
        file_path = self.knowledge_file.file.path
        self.assertTrue(os.path.exists(file_path))
        
        # Delete the chatbot
        self.chatbot.delete()
        
        # Verify DB deletion
        self.assertFalse(Chatbot.objects.filter(pk=self.chatbot.pk).exists())
        self.assertFalse(KnowledgeFile.objects.filter(pk=self.knowledge_file.pk).exists())
        self.assertFalse(KnowledgeChunk.objects.filter(pk=self.chunk.pk).exists())
        
        # Verify file deletion (Signal check)
        # Note: When cascading, the signal for KnowledgeFile should still fire
        self.assertFalse(os.path.exists(file_path), "File should be deleted when chatbot is deleted (cascade)")
