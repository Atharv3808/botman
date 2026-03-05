from django.urls import path
from .views import AnalyticsView, AnalyticsOverviewView, AnalyticsGraphView, AnalyticsLiveView

urlpatterns = [
    path('analytics/<int:chatbot_id>/', AnalyticsView.as_view(), name='chatbot-analytics'),
    path('analytics/<int:chatbot_id>/overview/', AnalyticsOverviewView.as_view(), name='analytics-overview'),
    path('analytics/<int:chatbot_id>/graph/', AnalyticsGraphView.as_view(), name='analytics-graph'),
    path('analytics/<int:chatbot_id>/live/', AnalyticsLiveView.as_view(), name='analytics-live'),
]
