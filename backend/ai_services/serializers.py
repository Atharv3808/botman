from rest_framework import serializers
from .models import ProviderConfiguration, ProviderAuditLog

class ProviderConfigurationSerializer(serializers.ModelSerializer):
    credentials = serializers.DictField(write_only=True, required=False)
    has_credentials = serializers.SerializerMethodField()

    class Meta:
        model = ProviderConfiguration
        fields = [
            'id', 'provider_type', 'name', 'config_data', 
            'credentials', 'has_credentials', 'is_active', 
            'version', 'parent_config', 'created_by', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'version', 'parent_config', 'created_by', 'created_at', 'updated_at']

    def get_has_credentials(self, obj):
        return bool(obj.encrypted_credentials)

    def create(self, validated_data):
        credentials = validated_data.pop('credentials', {})
        instance = ProviderConfiguration.objects.create(**validated_data)
        if credentials:
            instance.set_credentials(credentials)
            instance.save()
        return instance

    def update(self, instance, validated_data):
        credentials = validated_data.pop('credentials', None)
        
        # Implementation for versioning
        # When updating, we create a new version
        new_version = ProviderConfiguration.objects.create(
            provider_type=validated_data.get('provider_type', instance.provider_type),
            name=validated_data.get('name', instance.name),
            config_data=validated_data.get('config_data', instance.config_data),
            is_active=validated_data.get('is_active', instance.is_active),
            version=instance.version + 1,
            parent_config=instance.parent_config or instance,
            created_by=instance.created_by # In view we should set this to current user
        )
        
        if credentials is not None:
            new_version.set_credentials(credentials)
        else:
            # Copy old credentials if not provided
            new_version.encrypted_credentials = instance.encrypted_credentials
        
        new_version.save()
        
        # Deactivate old version
        instance.is_active = False
        instance.save()
        
        return new_version

class ProviderAuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderAuditLog
        fields = '__all__'
