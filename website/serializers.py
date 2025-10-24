from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .models import Registration, Product, ProductDocument, ProductRegistration


class UserSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "first_name",
                  "last_name", "email", "password", "confirm_password"]
        extra_kwargs = {
            "password": {"write_only": True},
            "username": {"error_messages": {"required": "Username is required"}},
            "email": {"error_messages": {"required": "Email is required", "invalid": "Please enter a valid email address"}},
            "first_name": {"error_messages": {"required": "First name is required"}},
            "last_name": {"error_messages": {"required": "Last name is required"}},
        }

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "This username is already taken. Please choose another one.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "This email is already registered. Please use a different email or try logging in.")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError(
                "Passwords do not match. Please make sure both password fields are identical.")
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
        extra_kwargs = {
            "user_type": {"error_messages": {"required": "Please select your organization type"}},
            "contact_number": {"error_messages": {"required": "Contact number is required"}},
            "country": {"error_messages": {"required": "Country is required"}},
            "state": {"error_messages": {"required": "State is required"}},
            "city": {"error_messages": {"required": "City is required"}},
            "pincode": {"error_messages": {"required": "Pincode is required"}},
        }

    def validate_contact_number(self, value):
        # Basic phone number validation
        if len(value) < 10:
            raise serializers.ValidationError(
                "Please enter a valid contact number with at least 10 digits.")
        return value

    def validate_pincode(self, value):
        # Basic pincode validation
        if not value.isdigit() or len(value) < 4:
            raise serializers.ValidationError("Please enter a valid pincode.")
        return value

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        # Remove confirm_password before creating user
        user_data.pop('confirm_password', None)
        user = User.objects.create_user(**user_data)
        registration = Registration.objects.create(user=user, **validated_data)
        return registration


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                "Your current password is incorrect.")
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("New passwords do not match.")
        return attrs

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "No account found with this email address.")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    uidb64 = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")

        try:
            uid = force_str(urlsafe_base64_decode(attrs['uidb64']))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("Invalid reset link.")

        if not default_token_generator.check_token(user, attrs['token']):
            raise serializers.ValidationError("Invalid or expired reset link.")

        attrs['user'] = user
        return attrs

    def save(self):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class ProductDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductDocument
        fields = ['id', 'document_name', 'file', 'uploaded_at']
        read_only_fields = ['uploaded_at']


class ProductRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductRegistration
        fields = [
            'id', 'country', 'registration_status', 'registration_number',
            'registration_date', 'expiry_date', 'remarks'
        ]


class ProductSerializer(serializers.ModelSerializer):
    documents = ProductDocumentSerializer(many=True, read_only=True)
    registrations = ProductRegistrationSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'product_name', 'biocontrol_agent_name', 'biocontrol_agent_strain',
            'accession_number', 'category', 'formulation', 'created_at', 'updated_at',
            'documents', 'registrations'
        ]
        read_only_fields = ['created_at', 'updated_at']
