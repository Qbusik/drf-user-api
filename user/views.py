from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.encoding import force_str, force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from user.serializers import UserSerializer


class CreateUserView(generics.CreateAPIView):
    """
    Register a new user, and send email confirmation message.
    """

    serializer_class = UserSerializer
    permission_classes = []

    def perform_create(self, serializer):
        user = serializer.save()

        token = PasswordResetTokenGenerator().make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        email_body = render_to_string(
            "verify_email.html",
            {
                "user": user,
                "uid": uid,
                "token": token,
                "domain": self.request.get_host(),
            },
        )

        email = EmailMessage(
            subject="Verify your email", body=email_body, to=[user.email]
        )

        email.send()


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
    Verify user email.
    """

    def get(self, request, uidb64, token):

        token_generator = PasswordResetTokenGenerator()

        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = get_user_model().objects.get(pk=user_id)

        except (TypeError, ValueError, OverflowError, ObjectDoesNotExist):
            return Response({"error": "Invalid link"}, status=400)

        if user.email_confirmed:
            return Response({"message": "Email already verified"})

        if token_generator.check_token(user, token):
            user.email_confirmed = True
            user.save(update_fields=["email_confirmed"])

            return Response({"message": "Email verified successfully"})

        return Response({"error": "Invalid token"}, status=400)
