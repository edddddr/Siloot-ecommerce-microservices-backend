from django.urls import path
from .views import InternalTokenView, RefreshTokenView, RegisterView, LoginView, LogoutView

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("login/", LoginView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("refresh/", RefreshTokenView.as_view(), name="token_refresh"),
]

urlpatterns += [
    path("internal/token/", InternalTokenView.as_view())
]