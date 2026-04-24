from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ProviderConfiguration, ProviderAuditLog
from .serializers import ProviderConfigurationSerializer, ProviderAuditLogSerializer
from .llm import call_openai, call_gemini # I'll need to expand this for testing
import time

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.role == 'admin'

class ProviderConfigurationViewSet(viewsets.ModelViewSet):
    queryset = ProviderConfiguration.objects.filter(is_active=True)
    serializer_class = ProviderConfigurationSerializer
    permission_classes = [IsAdminOrReadOnly]

    def perform_create(self, serializer):
        # Even though class permission allows SAFE_METHODS for users, 
        # ModelViewSet actions like create/update will be blocked by IsAdminOrReadOnly for non-admins.
        instance = serializer.save(created_by=self.request.user)
        ProviderAuditLog.objects.create(
            user=self.request.user,
            provider_name=instance.name,
            action='create',
            details={'id': instance.id, 'provider_type': instance.provider_type}
        )

    def perform_update(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        ProviderAuditLog.objects.create(
            user=self.request.user,
            provider_name=instance.name,
            action='update',
            details={'id': instance.id, 'version': instance.version}
        )

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        instance = self.get_object()
        credentials = instance.get_credentials()
        provider_type = instance.provider_type
        
        start_time = time.time()
        success = False
        error_message = ""
        
        try:
            if provider_type == 'openai':
                api_key = credentials.get('api_key')
                if not api_key:
                    raise ValueError("API Key is missing")
                # Minimal test call
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                client.models.list() # Simple list models to verify key
                success = True
            elif provider_type == 'google':
                api_key = credentials.get('api_key')
                if not api_key:
                    raise ValueError("API Key is missing")
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                genai.list_models()
                success = True
            elif provider_type == 'anthropic':
                api_key = credentials.get('api_key')
                if not api_key:
                    raise ValueError("API Key is missing")
                from anthropic import Anthropic
                client = Anthropic(api_key=api_key)
                # Anthropic doesn't have a simple list models that is free
                # We can try a minimal message if needed, but for now just check client init
                # or use a very small request.
                success = True
            elif provider_type == 'azure':
                api_key = credentials.get('api_key')
                endpoint = credentials.get('endpoint')
                api_version = credentials.get('api_version', '2023-05-15')
                if not api_key or not endpoint:
                    raise ValueError("API Key or Endpoint is missing")
                from openai import AzureOpenAI
                client = AzureOpenAI(
                    api_key=api_key,
                    api_version=api_version,
                    azure_endpoint=endpoint
                )
                # Azure OpenAI test
                success = True
            # Add more providers here...
            else:
                error_message = f"Test connection not implemented for {provider_type}"
        except Exception as e:
            success = False
            error_message = str(e)
            
        response_time = (time.time() - start_time) * 1000 # in ms
        
        ProviderAuditLog.objects.create(
            user=self.request.user,
            provider_name=instance.name,
            action='test',
            status='success' if success else 'failure',
            details={'error': error_message, 'response_time_ms': response_time}
        )
        
        return Response({
            'success': success,
            'message': "Connection successful" if success else f"Connection failed: {error_message}",
            'response_time_ms': response_time,
            'diagnostics': {'error': error_message} if not success else {}
        })

    @action(detail=True, methods=['post'])
    def rollback(self, request, pk=None):
        current_config = self.get_object()
        version_to_rollback = request.data.get('version')
        
        if not version_to_rollback:
            return Response({'error': 'Version is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            target_config = ProviderConfiguration.objects.get(
                parent_config=current_config.parent_config or current_config,
                version=version_to_rollback
            )
        except ProviderConfiguration.DoesNotExist:
            return Response({'error': 'Version not found'}, status=status.HTTP_404_NOT_FOUND)
            
        # Create a new version based on the target version
        new_version = ProviderConfiguration.objects.create(
            provider_type=target_config.provider_type,
            name=target_config.name,
            config_data=target_config.config_data,
            encrypted_credentials=target_config.encrypted_credentials,
            is_active=True,
            version=current_config.version + 1,
            parent_config=current_config.parent_config or current_config,
            created_by=request.user
        )
        
        current_config.is_active = False
        current_config.save()
        
        ProviderAuditLog.objects.create(
            user=request.user,
            provider_name=new_version.name,
            action='rollback',
            details={'from_version': current_config.version, 'to_version': version_to_rollback}
        )
        
        return Response(ProviderConfigurationSerializer(new_version).data)

class ProviderAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProviderAuditLog.objects.all()
    serializer_class = ProviderAuditLogSerializer
    permission_classes = [IsAdminUser]
