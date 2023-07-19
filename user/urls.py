from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import BlacklistTokenView, UserRegistration, TokenObtainView, VerifyEmail

urlpatterns = [
    path("register/", UserRegistration.as_view(), name="user_registration"),
    path("token/", TokenObtainView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/blacklist/", BlacklistTokenView.as_view(), name="black_list"),
    path(
        "verify-email/<str:uidb64>/<str:token>/",
        VerifyEmail.as_view(),
        name="verify_email",
    ),
]
