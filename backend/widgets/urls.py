from django.urls import path
from .views import WidgetConfigView, WidgetSessionView, WidgetChatView

urlpatterns = [
    path('config/<uuid:widget_token>/', WidgetConfigView.as_view(), name='widget-config'),
    path('session/', WidgetSessionView.as_view(), name='widget-session'),
    path('chat/', WidgetChatView.as_view(), name='widget-chat'),
]
