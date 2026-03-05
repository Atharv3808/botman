"""
URL configuration for botman_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from conversations.views import PublicChatView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('accounts.urls')),
    path('api/', include('chatbots.urls')),
    path('api/', include('knowledge.urls')),
    path('api/', include('conversations.urls')),
    path('api/', include('analytics.urls')),
    path('api/', include('health.urls')),
    path('widget/', include('widgets.urls')),
    path('public/chat/<uuid:widget_token>/', PublicChatView.as_view(), name='public_chat'),
]
