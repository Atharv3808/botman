from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import ChatbotViewSet

router = SimpleRouter()
router.register(r'chatbots', ChatbotViewSet, basename='chatbot')
router.register(r'bot', ChatbotViewSet, basename='bot')

urlpatterns = [
    path('', include(router.urls)),
]
