from django.urls import path
from .views import *

urlpatterns = [
    path("", Info.as_view()),
    path("create/", CreateUser.as_view()),
    path("login/", LogIn.as_view()),
    path("logout/", LogOut.as_view()),
    path("refresh/", RefreshView.as_view()),
]