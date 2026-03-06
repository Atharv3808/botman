from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSerializer
from .models import User, Subscription, Plan
from rest_framework_simplejwt.tokens import RefreshToken
import firebase_admin
from firebase_admin import auth, credentials
import os

# Initialize Firebase Admin SDK
# You should provide the path to your serviceAccountKey.json file via environment variable
service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
if service_account_path and os.path.exists(service_account_path):
    try:
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"Error initializing Firebase Admin: {e}")
else:
    # Initialize without explicit credentials (requires GOOGLE_APPLICATION_CREDENTIALS env var)
    try:
        firebase_admin.initialize_app()
    except Exception as e:
        print(f"Firebase Admin not initialized: {e}. Provide FIREBASE_SERVICE_ACCOUNT_PATH or GOOGLE_APPLICATION_CREDENTIALS.")

class SignupView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

class GoogleLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        id_token = request.data.get('id_token')
        if not id_token:
            return Response({"error": "No ID token provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Verify the Firebase ID token
            decoded_token = auth.verify_id_token(id_token)
            email = decoded_token.get('email')
            name = decoded_token.get('name', '')
            
            if not email:
                return Response({"error": "Email not found in token"}, status=status.HTTP_400_BAD_REQUEST)

            # Get or create user
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'first_name': name,
                    'is_active': True
                }
            )

            # Ensure user has a subscription if they are new or don't have one
            try:
                subscription = user.subscription
            except Subscription.DoesNotExist:
                free_plan = Plan.objects.get(name='Free')
                Subscription.objects.create(user=user, plan=free_plan)

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data,
                'is_new_user': created
            })

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ProtectedView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({
            "message": "This is a protected route",
            "user": request.user.username
        })
