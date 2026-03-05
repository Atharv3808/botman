from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from chatbots.models import Chatbot
from .models import KnowledgeFile, KnowledgeChunk
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
from ai_services.tasks import process_knowledge_file

User = get_user_model()

class KnowledgeStatusTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.chatbot = Chatbot.objects.create(
            name='Test Bot',
            owner=self.user
        )
        self.file1 = KnowledgeFile.objects.create(
            chatbot=self.chatbot,
            file=SimpleUploadedFile("test1.txt", b"content"),
            status='processing'
        )
        self.file2 = KnowledgeFile.objects.create(
            chatbot=self.chatbot,
            file=SimpleUploadedFile("test2.txt", b"content"),
            status='completed'
        )
        KnowledgeChunk.objects.create(
            chatbot=self.chatbot,
            knowledge_file=self.file2,
            content="chunk content",
            embedding=[0.1]*1536
        )

    def test_get_status(self):
        url = f'/api/knowledge/status/{self.chatbot.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Updated assertion based on new response structure
        self.assertIn('files', response.data)
        self.assertEqual(len(response.data['files']), 2)
        self.assertEqual(response.data['total_chunk_count'], 1)

    def test_get_status_invalid_chatbot(self):
        url = '/api/knowledge/status/999/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_status_unauthorized(self):
        other_user = User.objects.create_user(username='other', password='pw')
        other_chatbot = Chatbot.objects.create(name='Other Bot', owner=other_user)
        url = f'/api/knowledge/status/{other_chatbot.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class KnowledgePipelineTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.chatbot = Chatbot.objects.create(name='Test Bot', owner=self.user)
        self.file = SimpleUploadedFile("test_doc.txt", b"This is a test document.")
        self.knowledge_file = KnowledgeFile.objects.create(
            chatbot=self.chatbot,
            file=self.file,
            status='pending'
        )

    @patch('ai_services.tasks.OpenAI')
    @patch('ai_services.tasks.extract_text_from_file')
    @patch('ai_services.tasks.split_text')
    @override_settings(OPENAI_API_KEY='dummy')
    def test_process_knowledge_file_success(self, mock_split, mock_extract, mock_openai):
        # Setup mocks
        mock_extract.return_value = "This is a test document."
        mock_split.return_value = ["This is a test document."]
        
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_response = MagicMock()
        mock_embedding_data = MagicMock()
        mock_embedding_data.embedding = [0.1] * 1536
        mock_response.data = [mock_embedding_data]
        mock_client.embeddings.create.return_value = mock_response

        # Run task
        process_knowledge_file(self.knowledge_file.id)
        
        # Reload from DB
        self.knowledge_file.refresh_from_db()
        
        # Verify status and chunks
        self.assertEqual(self.knowledge_file.status, 'completed')
        self.assertEqual(self.knowledge_file.chunk_count, 1)
        self.assertIsNone(self.knowledge_file.processing_error)
        self.assertEqual(KnowledgeChunk.objects.count(), 1)

    @patch('ai_services.tasks.extract_text_from_file')
    def test_process_knowledge_file_failure(self, mock_extract):
        # Setup failure (e.g., extraction fails)
        mock_extract.side_effect = Exception("Extraction failed")
        
        # Run task
        process_knowledge_file(self.knowledge_file.id)
        
        # Reload from DB
        self.knowledge_file.refresh_from_db()
        
        # Verify status and error
        self.assertEqual(self.knowledge_file.status, 'failed')
        self.assertEqual(self.knowledge_file.processing_error, "Extraction failed")
