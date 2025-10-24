from django.shortcuts import render
from django.db import transaction
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from .models import Registration, Product, ProductDocument, ProductRegistration
from .serializers import (
    UserSerializer, RegistrationSerializer, ChangePasswordSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer, ProductSerializer,
    ProductDocumentSerializer, ProductRegistrationSerializer
)

# Create your views here.


class LoginView(generics.GenericAPIView):
    """
    User login endpoint - returns token
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {"detail": "Username and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)

        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {"detail": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )


class LogoutView(generics.GenericAPIView):
    """
    User logout endpoint - deletes token
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
            return Response(
                {"detail": "Successfully logged out"},
                status=status.HTTP_200_OK
            )
        except:
            return Response(
                {"detail": "Logout failed"},
                status=status.HTTP_400_BAD_REQUEST
            )


class RegistrationView(generics.CreateAPIView):
    """
    Registration profile creation endpoint with atomic transaction
    """
    queryset = Registration.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            serializer = RegistrationSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "success": True,
                    "message": "Registration completed successfully!",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    "success": False,
                    "message": "Please correct the errors below and try again.",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "success": False,
                "message": "An unexpected error occurred. Please try again later.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update user profile
    """
    serializer_class = RegistrationSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            return Registration.objects.get(user=self.request.user)
        except Registration.DoesNotExist:
            return None

    def get(self, request):
        profile = self.get_object()
        if profile:
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        return Response(
            {"detail": "Profile not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    def put(self, request):
        profile = self.get_object()
        if profile:
            serializer = self.get_serializer(
                profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {"detail": "Profile not found"},
            status=status.HTTP_404_NOT_FOUND
        )


class ChangePasswordView(generics.GenericAPIView):
    """
    Change password for authenticated users
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Password changed successfully!"
            }, status=status.HTTP_200_OK)
        return Response({
            "success": False,
            "message": "Please correct the errors below.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(generics.GenericAPIView):
    """
    Send password reset email
    """
    serializer_class = ForgotPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)

            # Generate reset token
            token = default_token_generator.make_token(user)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

            # Create reset URL (you'll need to configure this in your frontend)
            reset_url = f"http://localhost:3000/reset-password?token={token}&uid={uidb64}"

            # Send email (configure your email settings)
            try:
                send_mail(
                    'Password Reset Request',
                    f'Click the link to reset your password: {reset_url}',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                return Response({
                    "success": True,
                    "message": "Password reset link has been sent to your email."
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    "success": False,
                    "message": "Failed to send email. Please try again later.",
                    "error": str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "success": False,
            "message": "Please correct the errors below.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(generics.GenericAPIView):
    """
    Reset password using token
    """
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Password reset successfully! You can now login with your new password."
            }, status=status.HTTP_200_OK)

        return Response({
            "success": False,
            "message": "Please correct the errors below.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ProductListView(generics.ListAPIView):
    """
    Get all products with their documents and registrations
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            products = Product.objects.all()
            serializer = ProductSerializer(products, many=True)
            return Response({
                "success": True,
                "data": serializer.data,
                "count": products.count()
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to retrieve products.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductDetailView(generics.RetrieveAPIView):
    """
    Get a specific product with its documents and registrations
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
            serializer = ProductSerializer(product)
            return Response({
                "success": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({
                "success": False,
                "message": "Product not found."
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to retrieve product.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductDocumentListView(generics.ListAPIView):
    """
    Get all documents for a specific product
    """
    serializer_class = ProductDocumentSerializer
    permission_classes = [AllowAny]

    def get(self, request, product_id):
        try:
            product = Product.objects.get(pk=product_id)
            documents = ProductDocument.objects.filter(product=product)
            serializer = ProductDocumentSerializer(documents, many=True)
            return Response({
                "success": True,
                "data": serializer.data,
                "count": documents.count()
            }, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({
                "success": False,
                "message": "Product not found."
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to retrieve product documents.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductRegistrationListView(generics.ListAPIView):
    """
    Get all registrations for a specific product
    """
    serializer_class = ProductRegistrationSerializer
    permission_classes = [AllowAny]

    def get(self, request, product_id):
        try:
            product = Product.objects.get(pk=product_id)
            registrations = ProductRegistration.objects.filter(product=product)
            serializer = ProductRegistrationSerializer(
                registrations, many=True)
            return Response({
                "success": True,
                "data": serializer.data,
                "count": registrations.count()
            }, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({
                "success": False,
                "message": "Product not found."
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to retrieve product registrations.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
