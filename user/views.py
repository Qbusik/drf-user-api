from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from django.core.cache import cache
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .tasks import send_verification_email
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from user.serializers import (
    UserSerializer,
    LogoutSerializer,
    UpdateUserSerializer,
    ChangePasswordSerializer,
)


@extend_schema(
    summary="Register user",
    description="Creates a new user and sends a verification email asynchronously.",
)
class CreateUserView(generics.CreateAPIView):

    serializer_class = UserSerializer
    permission_classes = []

    def perform_create(self, serializer):

        user = serializer.save()

        send_verification_email.delay(
            user_id=user.id,
            domain=self.request.get_host(),
        )


@extend_schema(
    summary="Resend verification email",
    description="Resends verification email with a 10-second cooldown between requests.",
)
class ResendVerificationEmailView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        user = request.user

        if user.email_confirmed:
            return Response({"detail": "Already verified"}, status=400)

        cache_key = f"resend_verification:{user.id}"

        if cache.get(cache_key):
            return Response(
                {"error": "Wait before resending"},
                status=429,
            )

        send_verification_email.delay(
            user_id=user.id,
            domain=request.get_host(),
        )

        cache.set(cache_key, True, timeout=10)

        return Response({"detail": "Email sent"}, status=200)


@extend_schema(
    summary="Get user profile",
    description="Retrieve user's profile.",
)
class RetrieveUserView(generics.RetrieveAPIView):

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema(
    summary="Update user profile",
    description="Updates authenticated user's profile data.",
)
class UpdateUserView(generics.UpdateAPIView):

    serializer_class = UpdateUserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema(
    summary="Change password",
    description="Change the user password by providing the current and new password.",
    request=ChangePasswordSerializer,
    responses={200: None},
)
class ChangePasswordView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)

        user = request.user
        new_password = serializer.validated_data["new_password"]

        user.set_password(new_password)
        user.save()

        return Response(
            {"detail": "Password changed successfully"},
            status=status.HTTP_200_OK,
        )


@extend_schema(
    summary="Verify email (email link)",
    description=(
        "This endpoint is triggered via a verification link sent to the user's email. "
        "It is not intended to be called manually from Swagger UI."
    ),
    responses={200: None},
)
class VerifyEmailView(APIView):
    """
    Verify user's email and render a confirmation page.
    """

    def get(self, request, uidb64, token):

        token_generator = PasswordResetTokenGenerator()

        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = get_user_model().objects.get(pk=user_id)

        except (TypeError, ValueError, OverflowError, ObjectDoesNotExist):

            return render(
                request,
                "verify_response.html",
                {
                    "title": "Invalid Link",
                    "message": "Verification link is invalid.",
                },
                status=400,
            )

        if user.email_confirmed:

            return render(
                request,
                "verify_response.html",
                {
                    "title": "Already Verified",
                    "message": "Your email is already verified.",
                },
            )

        if token_generator.check_token(user, token):

            user.email_confirmed = True

            user.save(update_fields=["email_confirmed"])

            return render(
                request,
                "verify_response.html",
                {
                    "title": "Email Verified",
                    "message": "Your email has been verified successfully.",
                },
            )

        return render(
            request,
            "verify_response.html",
            {
                "title": "Invalid Token",
                "message": "Verification token is invalid or expired.",
            },
            status=400,
        )


@extend_schema(
    summary="Logout user",
    description="Blacklists refresh token.",
    request=LogoutSerializer,
    responses={205: None},
)
class LogoutView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            refresh_token = serializer.validated_data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"detail": "Successfully logged out"},
                status=status.HTTP_205_RESET_CONTENT,
            )

        except TokenError:
            return Response(
                {"detail": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST,
            )
