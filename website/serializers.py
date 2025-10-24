from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Registration


class UserSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "first_name",
                  "last_name", "email", "password", "confirm_password"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user


class RegistrationSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Registration
        fields = [
            "id", "user", "user_type", "contact_number", "designation",
            "country", "state", "district", "city", "pincode", "website",
            "is_verified", "created_at", "updated_at",
        ]
        read_only_fields = ["is_verified", "created_at", "updated_at"]

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        # Remove confirm_password before creating user
        user_data.pop('confirm_password', None)
        user = User.objects.create_user(**user_data)
        registration = Registration.objects.create(user=user, **validated_data)
        return registration
