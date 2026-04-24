from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import ProviderConfigurationViewSet, ProviderAuditLogViewSet

router = SimpleRouter()
router.register(r'providers', ProviderConfigurationViewSet, basename='provider-configuration')
router.register(r'provider-logs', ProviderAuditLogViewSet, basename='provider-audit-log')

urlpatterns = [
    path('', include(router.urls)),
]
