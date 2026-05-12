from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from user.views import (
    CreateUserView,
    RetrieveUserView,
    UpdateUserView,
    VerifyEmailView,
    ResendVerificationEmailView,
    LogoutView,
    ChangePasswordView,
    ResetPasswordView,
    ForgotPasswordView,
)

app_name = "user"

urlpatterns = [
    path("", CreateUserView.as_view(), name="register"),
    path(
        "verify-email/<uidb64>/<token>/",
        VerifyEmailView.as_view(),
        name="verify_email",
    ),
    path(
        "me/resend-verification-email/",
        ResendVerificationEmailView.as_view(),
        name="resend_verification_email",
    ),
    path("forget-password/", ForgotPasswordView.as_view(), name="forget_password"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset_password"),
    path("me/", RetrieveUserView.as_view(), name="retrieve_user"),
    path("me/update/", UpdateUserView.as_view(), name="update_user"),
    path("me/change-password/", ChangePasswordView.as_view(), name="change_password"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
