from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import KnowledgeViewSet

router = SimpleRouter()
router.register(r'knowledge', KnowledgeViewSet, basename='knowledge')

urlpatterns = [
    path('', include(router.urls)),
]
