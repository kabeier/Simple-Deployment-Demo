from django.contrib.auth import login, authenticate, logout
from .models import AppUser
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status as s
from django.conf import settings

COOKIE_MAX_AGE = 60 * 60 * 24 * 7 # 7 days long

def set_token_cookie(response, token_key):
    response.set_cookie(
        key = "token",
        value=token_key,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        max_age=COOKIE_MAX_AGE,
        path="/"
    )
    return response

class CookieAuthentication(TokenAuthentication):
    """Reads the DRF token from an httpOnly cookie instead of the Auth header"""
    
    def authenticate(self, request):
        token_key = request.COOKIES.get("token")
        if not token_key:
            return None
        return self.authenticate_credentials(token_key)
        

# Create your views here.
class CreateUser(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        data = request.data
        data['username'] = request.data.get('email')
        try:
            new_user = AppUser.objects.create_user(**data)
            new_user.full_clean()
            new_user.save()
            token = Token.objects.create(user=new_user)
            response = Response({"email":new_user.email}, status=s.HTTP_201_CREATED)
            return set_token_cookie(response, token.key)
        except Exception as e:
            return Response(e.args, status=s.HTTP_400_BAD_REQUEST)

class LogIn(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        data = request.data
        data['username'] = request.data.get('email')
        user = authenticate(username=data.get('username'), password=data.get("password"))
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            response = Response({ "email":user.email})
            return set_token_cookie(response, token.key)
        else:
            return Response("No user matching credentials", status=s.HTTP_404_NOT_FOUND)

class UserView(APIView):
    authentication_classes = [CookieAuthentication]
    permission_classes = [IsAuthenticated]


class Info(UserView):
    def get(self, request):
        user = request.user
        return Response({"email":user.email})

class LogOut(UserView):
    def post(self, request):
        user = request.user
        user.auth_token.delete()
        response = Response({"detail":"logged out"})
        response.delete_cookie("token", path="/")