from django.urls import path
from rest_framework_simplejwt.views import TokenVerifyView

from .views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    EmailVerificationView,
    LogoutAPIView,
    PasswordResetView,
    RegisterView,
    ResendVerificationEmailView,
    TokenInfoAPIView,
    UserBulkApproveView,
    UserListView,
    UserPasswordChangeAPIView,
    UserProfileView,
    VerifyEmailView,
)

app_name = "user"

urlpatterns = [
    # Auth & User Management
    path("signup/", RegisterView.as_view(), name="signup"),
    path("verify/email/", VerifyEmailView.as_view(), name="verify_email"),
    path("password-change/", UserPasswordChangeAPIView.as_view(), name="password_change"),
    path("password-reset/", PasswordResetView.as_view(), name="password-reset"),
    # JWT Auth
    path("token/login/", CustomTokenObtainPairView.as_view(), name="token_login"),
    path("token/logout/", LogoutAPIView.as_view(), name="token_logout"),
    path("token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("token/info/", TokenInfoAPIView.as_view(), name="token_info"),
    # User Resources (list/create, detail, profile)
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/bulk-approve/", UserBulkApproveView.as_view(), name="user-bulk-approve"),
    path("users/me/", UserProfileView.as_view(), name="user-profile"),
    path("verify-email/", EmailVerificationView.as_view(), name="verify-email"),
    path(
        "resend-verification-email/",
        ResendVerificationEmailView.as_view(),
        name="resend-verification-email",
    ),
]
