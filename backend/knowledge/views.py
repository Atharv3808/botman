
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import KnowledgeFile, KnowledgeChunk
from .serializers import KnowledgeFileSerializer
from chatbots.models import Chatbot
from ai_services.tasks import process_knowledge_file

class KnowledgeViewSet(viewsets.ModelViewSet):
    serializer_class = KnowledgeFileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return files for chatbots owned by the user
        return KnowledgeFile.objects.filter(chatbot__owner=self.request.user)

    @action(detail=False, methods=['post'])
    def upload(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Check ownership of the chatbot
            chatbot = serializer.validated_data['chatbot']
            if chatbot.owner != request.user:
                return Response(
                    {"detail": "You do not own this chatbot."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Save file (status defaults to 'pending')
            instance = serializer.save()
            
            # Trigger async processing
            process_knowledge_file.delay(instance.id)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='status/(?P<chatbot_id>\\d+)')
    def status(self, request, chatbot_id=None):
        try:
            chatbot = Chatbot.objects.get(id=chatbot_id, owner=request.user)
        except Chatbot.DoesNotExist:
            return Response(
                {"detail": "Chatbot not found or you do not own it."},
                status=status.HTTP_404_NOT_FOUND
            )

        files = KnowledgeFile.objects.filter(chatbot=chatbot)
        total_chunk_count = KnowledgeChunk.objects.filter(chatbot=chatbot).count()

        return Response({
            "files": KnowledgeFileSerializer(files, many=True).data,
            "total_chunk_count": total_chunk_count
        })

    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """
        Returns extracted chunks for a specific knowledge file.
        """
        knowledge_file = self.get_object() # Checks permission via get_queryset
        
        chunks = KnowledgeChunk.objects.filter(knowledge_file=knowledge_file).order_by('chunk_index')
        
        return Response({
            "file_id": knowledge_file.id,
            "filename": knowledge_file.file.name,
            "status": knowledge_file.status,
            "chunks": [
                {
                    "index": chunk.chunk_index,
                    "content": chunk.content,
                    "id": chunk.id
                }
                for chunk in chunks
            ]
        })
