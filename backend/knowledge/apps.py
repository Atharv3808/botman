from django.apps import AppConfig


class KnowledgeConfig(AppConfig):
    name = 'knowledge'

    def ready(self):
        import knowledge.signals
