from django.contrib.auth import  authenticate
from django.conf import settings
from .models import AppUser
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status as s

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.settings import api_settings

ACCESS_MAX_AGE = int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds())
REFRESH_MAX_AGE = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())
REFRESH_COOKIE_PATH = "/api/v1/users/"

def set_auth_cookies(response, access=None, refresh=None):
    common = {
        "httponly": True,
        "secure": settings.AUTH_COOKIE_SECURE,
        "samesite": settings.AUTH_COOKIE_SAMESITE,
    }
    if access:
        response.set_cookie("access", access, max_age=ACCESS_MAX_AGE, path="/", **common)
    if refresh:
        response.set_cookie("refresh", refresh, max_age=REFRESH_MAX_AGE,
                            path=REFRESH_COOKIE_PATH, **common)
    return response

def clear_auth_cookies(response):
    response.delete_cookie("access", path="/")
    response.delete_cookie("refresh", path=REFRESH_COOKIE_PATH)
    return response


def tokens_for(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)

class JWTCookieAuthentication(JWTAuthentication):
    """Read the JWT access token from an httpOnly cookie instead of the Authorization header."""
    def authenticate(self, request):
        raw_token = request.COOKIES.get("access")
        if raw_token is None:
            return None
        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token

    
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
            access, refresh = tokens_for(new_user)
            response = Response({"email":new_user.email}, status=s.HTTP_201_CREATED)
            return set_auth_cookies(response, access, refresh)
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
            access, refresh = tokens_for(user)
            response = Response({"email": user.email})
            return set_auth_cookies(response, access, refresh)
        else:
            return Response("No user matching credentials", status=s.HTTP_404_NOT_FOUND)

class RefreshView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        raw_refresh = request.COOKIES.get("refresh")
        if not raw_refresh:
            return Response({"detail": "No refresh token"}, status=s.HTTP_401_UNAUTHORIZED)

        try:
            # Turn the raw JWT string into a SimpleJWT RefreshToken object.
            #
            # Creating this object also validates the token.
            # If the token is malformed, expired, or otherwise invalid,
            # SimpleJWT will raise a TokenError.
            refresh = RefreshToken(raw_refresh)
        except TokenError:
            return clear_auth_cookies(
                Response({"detail": "Invalid or expired refresh token"},
                         status=s.HTTP_401_UNAUTHORIZED)
            )

        access = str(refresh.access_token)

        new_refresh = None
        
        # Check SimpleJWT's settings to see whether refresh-token
        # rotation has been enabled.
        #
        # Rotation means every time a refresh token is used,
        # we replace it with a newly generated refresh token.
        if api_settings.ROTATE_REFRESH_TOKENS:
            # If refresh-token blacklisting is also enabled,
            # invalidate the old refresh token after it has been used.
            if api_settings.BLACKLIST_AFTER_ROTATION:
                try:
                    refresh.blacklist()
                except AttributeError:
                    pass
            
            # Give the refresh token a new unique JWT ID ("jti").
            #
            # This helps distinguish the new rotated token from
            # the old refresh token.
            refresh.set_jti()
            # new expiration time
            refresh.set_exp()
            # new "issued at" timestamp
            refresh.set_iat()
            new_refresh = str(refresh)

        response = Response({"refreshed": True})
        return set_auth_cookies(response, access, new_refresh)


class UserView(APIView):
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]


class Info(UserView):
    def get(self, request):
        user = request.user
        return Response({"email":user.email})

class LogOut(UserView):
    def post(self, request):
        raw_refresh = request.COOKIES.get("refresh")
        if raw_refresh:
            try:
                RefreshToken(raw_refresh).blacklist()
            except TokenError:
                pass
        return clear_auth_cookies(Response({"detail": "logged out"}))