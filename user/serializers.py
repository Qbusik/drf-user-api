from django.contrib.auth import get_user_model
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("id", "email", "first_name", "last_name", "password")
        extra_kwargs = {"password": {"write_only": True, "min_length": 5}}

    def create(self, validated_data):
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)

        email_changed = (
            "email" in validated_data and validated_data["email"] != instance.email
        )

        user = super().update(instance, validated_data)

        changed = False

        if password:
            user.set_password(password)
            changed = True

        if email_changed:
            user.email_confirmed = False
            changed = True

        if changed:
            user.save()

        return user

    def validate_email(self, value):
        value = value.lower()
        user = self.instance
        qs = get_user_model().objects.filter(email=value)
        if user:
            qs = qs.exclude(pk=user.pk)
        if qs.exists():
            raise serializers.ValidationError("Email already exists")

        return value


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
