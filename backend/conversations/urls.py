from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import ChatViewSet, ConversationHistoryViewSet, DebugRAGView

router = SimpleRouter()
router.register(r'chat', ChatViewSet, basename='chat')
router.register(r'history', ConversationHistoryViewSet, basename='conversation-history')

urlpatterns = [
    path('debug/rag-test/', DebugRAGView.as_view(), name='debug-rag-test'),
    path('', include(router.urls)),
]
