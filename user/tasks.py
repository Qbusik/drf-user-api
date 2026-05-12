from celery import shared_task
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


@shared_task(bind=True, max_retries=3)
def send_verification_email(self, user_id, domain):

    try:
        User = get_user_model()

        user = User.objects.get(pk=user_id)

        token = PasswordResetTokenGenerator().make_token(user)

        uid = urlsafe_base64_encode(force_bytes(user.pk))

        email_body = render_to_string(
            "verify_email.html",
            {
                "user": user,
                "uid": uid,
                "token": token,
                "domain": domain,
            },
        )

        email = EmailMessage(
            subject="Verify your email",
            body=email_body,
            to=[user.email],
        )

        email.content_subtype = "html"

        email.send()

    except Exception as exc:
        raise self.retry(exc=exc, countdown=10)


@shared_task(bind=True, max_retries=3)
def send_reset_password_email(self, user_id, code):

    try:
        User = get_user_model()

        user = User.objects.get(pk=user_id)

        email_body = render_to_string(
            "reset_pwd_email.html",
            {
                "user": user,
                "code": code,
            },
        )

        email = EmailMessage(
            subject="Password reset",
            body=email_body,
            to=[user.email],
        )

        email.content_subtype = "html"

        email.send()

    except Exception as exc:
        raise self.retry(exc=exc, countdown=10)
