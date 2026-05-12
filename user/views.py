from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from rest_framework.response import Response
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken

from .tasks import send_verification_email
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from user.serializers import UserSerializer, LogoutSerializer


class CreateUserView(generics.CreateAPIView):
    """
    Register a new user, and send verification email.
    """

    serializer_class = UserSerializer
    permission_classes = []

    def perform_create(self, serializer):

        user = serializer.save()

        send_verification_email.delay(
            user_id=user.id,
            domain=self.request.get_host(),
        )


class ResendVerificationEmailView(APIView):
    """
    Resend verification email.
    """

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


class ManageUserView(generics.RetrieveUpdateAPIView):
    """
    Retrieve and update user's profile.
    """

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


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

        except Exception:
            return Response(
                {"detail": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST,
            )
