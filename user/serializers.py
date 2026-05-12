from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers


class EmailLowercaseUniqueMixin:
    def validate_email(self, value):
        value = value.lower()
        qs = get_user_model().objects.filter(email=value)

        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError("Email already exists")

        return value


class UserSerializer(EmailLowercaseUniqueMixin, serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("id", "email", "first_name", "last_name", "password")
        extra_kwargs = {"password": {"write_only": True, "min_length": 5}}

    def create(self, validated_data):
        return get_user_model().objects.create_user(**validated_data)

    def validate_password(self, value):
        validate_password(value)
        return value


class UpdateUserSerializer(EmailLowercaseUniqueMixin, serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("id", "email", "first_name", "last_name")

    def update(self, instance, validated_data):
        email_changed = (
            "email" in validated_data and validated_data["email"] != instance.email
        )

        user = super().update(instance, validated_data)

        changed = False

        if email_changed:
            user.email_confirmed = False
            changed = True

        if changed:
            user.save()

        return user


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        user = self.context["request"].user
        current_password = attrs.get("current_password")

        if not user.check_password(current_password):
            raise serializers.ValidationError(
                {"current_password": "Incorrect password"}
            )

        return attrs


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
