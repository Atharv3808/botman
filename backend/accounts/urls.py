from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import SignupView, ProtectedView, GoogleLoginView

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('google/', GoogleLoginView.as_view(), name='google_login'),
    path('protected/', ProtectedView.as_view(), name='protected'),
]
