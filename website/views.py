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
from .models import Registration, Product, ProductDocument, ProductRegistration, Membership, MembershipDocument, MembershipPayment, Quotation, QuotationItem, QuotationGuidelineFile
from .serializers import (
    UserSerializer, RegistrationSerializer, ChangePasswordSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer, ProductSerializer,
    ProductDocumentSerializer, ProductRegistrationSerializer, MembershipSerializer,
    MembershipDocumentSerializer, MembershipPaymentSerializer, QuotationSerializer, QuotationItemSerializer, QuotationGuidelineFileSerializer
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

            # Get registration ID if exists
            try:
                registration = Registration.objects.get(user=user)
                registration_id = registration.id
            except Registration.DoesNotExist:
                registration_id = None

            return Response({
                'token': token.key,
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'registration_id': registration_id,
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
            # Print request data to terminal
            print("\n" + "="*50)
            print("📤 REGISTRATION POST REQUEST")
            print("="*50)
            print(f"🔗 URL: {request.get_full_path()}")
            print(f"📋 Method: {request.method}")
            print(f"📦 Content-Type: {request.content_type}")
            print("\n📊 REQUEST DATA:")
            print("-" * 30)

            # Print form data
            if hasattr(request, 'data'):
                for key, value in request.data.items():
                    if key == 'password' or key == 'confirm_password':
                        print(f"  {key}: {'*' * len(str(value))}")
                    else:
                        print(f"  {key}: {value}")

            print("="*50)

            serializer = RegistrationSerializer(data=request.data)
            if serializer.is_valid():
                registration = serializer.save()
                print(
                    f"✅ Registration created successfully with ID: {registration.id}")
                return Response({
                    "success": True,
                    "message": "Registration completed successfully!",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                print(f"❌ Validation errors: {serializer.errors}")
                return Response({
                    "success": False,
                    "message": "Please correct the errors below and try again.",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"💥 Server error: {str(e)}")
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


class MembershipListView(generics.ListCreateAPIView):
    """
    Get user's memberships or create a new membership
    """
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Print request info for debugging
            print("\n" + "="*50)
            print("📤 MEMBERSHIP LIST GET REQUEST")
            print("="*50)
            print(f"🔗 URL: {request.get_full_path()}")
            print(f"🔐 User: {request.user}")
            print(f"📋 Method: {request.method}")
            print("="*50)

            # Get user's registration
            try:
                user_registration = Registration.objects.get(user=request.user)
                print(f"👤 User Registration ID: {user_registration.id}")

                # Filter memberships by user's registration
                memberships = Membership.objects.filter(
                    registration=user_registration)
                print(f"📊 Found {memberships.count()} memberships for user")

            except Registration.DoesNotExist:
                print("❌ User has no registration")
                return Response({
                    "success": False,
                    "message": "User registration not found. Please complete your registration first.",
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = MembershipSerializer(memberships, many=True)
            print(f"✅ Returning {len(serializer.data)} memberships")

            return Response({
                "success": True,
                "data": serializer.data,
                "count": memberships.count(),
                "user_registration_id": user_registration.id
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"💥 Server error: {str(e)}")
            return Response({
                "success": False,
                "message": "Failed to retrieve memberships.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            serializer = MembershipSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "success": True,
                    "message": "Membership created successfully!",
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


class MembershipDetailView(generics.RetrieveUpdateAPIView):
    """
    Get or update a specific membership with its documents and payments
    """
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            # Print request info for debugging
            print("\n" + "="*50)
            print("📤 MEMBERSHIP DETAIL GET REQUEST")
            print("="*50)
            print(f"🔗 URL: {request.get_full_path()}")
            print(f"🔐 User: {request.user}")
            print(f"📋 Method: {request.method}")
            print(f"🆔 Requested Membership ID: {pk}")
            print("="*50)

            # Get user's registration
            try:
                user_registration = Registration.objects.get(user=request.user)
                print(f"👤 User Registration ID: {user_registration.id}")

                # Get membership and verify it belongs to the user
                membership = Membership.objects.get(
                    pk=pk, registration=user_registration)
                print(f"✅ Membership {pk} belongs to user")

            except Registration.DoesNotExist:
                print("❌ User has no registration")
                return Response({
                    "success": False,
                    "message": "User registration not found. Please complete your registration first.",
                }, status=status.HTTP_404_NOT_FOUND)
            except Membership.DoesNotExist:
                print(f"❌ Membership {pk} not found or doesn't belong to user")
                return Response({
                    "success": False,
                    "message": "Membership not found or you don't have permission to access it."
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = MembershipSerializer(membership)
            print(f"✅ Returning membership data")

            return Response({
                "success": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"💥 Server error: {str(e)}")
            return Response({
                "success": False,
                "message": "Failed to retrieve membership.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk):
        try:
            # Print request info for debugging
            print("\n" + "="*50)
            print("📤 MEMBERSHIP UPDATE PUT REQUEST")
            print("="*50)
            print(f"🔗 URL: {request.get_full_path()}")
            print(f"🔐 User: {request.user}")
            print(f"📋 Method: {request.method}")
            print(f"🆔 Requested Membership ID: {pk}")
            print("="*50)

            # Get user's registration
            try:
                user_registration = Registration.objects.get(user=request.user)
                print(f"👤 User Registration ID: {user_registration.id}")

                # Get membership and verify it belongs to the user
                membership = Membership.objects.get(
                    pk=pk, registration=user_registration)
                print(f"✅ Membership {pk} belongs to user")

            except Registration.DoesNotExist:
                print("❌ User has no registration")
                return Response({
                    "success": False,
                    "message": "User registration not found. Please complete your registration first.",
                }, status=status.HTTP_404_NOT_FOUND)
            except Membership.DoesNotExist:
                print(f"❌ Membership {pk} not found or doesn't belong to user")
                return Response({
                    "success": False,
                    "message": "Membership not found or you don't have permission to update it."
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = MembershipSerializer(
                membership, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                print(f"✅ Membership {pk} updated successfully")
                return Response({
                    "success": True,
                    "message": "Membership updated successfully!",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)
            else:
                print(f"❌ Validation errors: {serializer.errors}")
                return Response({
                    "success": False,
                    "message": "Please correct the errors below and try again.",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(f"💥 Server error: {str(e)}")
            return Response({
                "success": False,
                "message": "An unexpected error occurred. Please try again later.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MembershipDocumentListView(generics.ListCreateAPIView):
    """
    Get all documents for a specific membership or create a new document
    """
    serializer_class = MembershipDocumentSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, membership_id):
        try:
            membership = Membership.objects.get(pk=membership_id)
            documents = MembershipDocument.objects.filter(
                membership=membership)
            serializer = MembershipDocumentSerializer(documents, many=True)
            return Response({
                "success": True,
                "data": serializer.data,
                "count": documents.count()
            }, status=status.HTTP_200_OK)
        except Membership.DoesNotExist:
            return Response({
                "success": False,
                "message": "Membership not found."
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to retrieve membership documents.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, membership_id):
        try:
            membership = Membership.objects.get(pk=membership_id)
            data = request.data.copy()
            data['membership'] = membership.id

            serializer = MembershipDocumentSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "success": True,
                    "message": "Document uploaded successfully!",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    "success": False,
                    "message": "Please correct the errors below and try again.",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Membership.DoesNotExist:
            return Response({
                "success": False,
                "message": "Membership not found."
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "success": False,
                "message": "An unexpected error occurred. Please try again later.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MembershipPaymentListView(generics.ListCreateAPIView):
    """
    Get all payments for a specific membership or create a new payment
    """
    serializer_class = MembershipPaymentSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, membership_id):
        try:
            membership = Membership.objects.get(pk=membership_id)
            payments = MembershipPayment.objects.filter(membership=membership)
            serializer = MembershipPaymentSerializer(payments, many=True)
            return Response({
                "success": True,
                "data": serializer.data,
                "count": payments.count()
            }, status=status.HTTP_200_OK)
        except Membership.DoesNotExist:
            return Response({
                "success": False,
                "message": "Membership not found."
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to retrieve membership payments.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, membership_id):
        try:
            membership = Membership.objects.get(pk=membership_id)
            data = request.data.copy()
            data['membership'] = membership.id

            serializer = MembershipPaymentSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "success": True,
                    "message": "Payment recorded successfully!",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    "success": False,
                    "message": "Please correct the errors below and try again.",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Membership.DoesNotExist:
            return Response({
                "success": False,
                "message": "Membership not found."
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "success": False,
                "message": "An unexpected error occurred. Please try again later.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------------------------------------------------
# MEMBERSHIP DOCUMENT API - Dedicated endpoints for membership documents
# ------------------------------------------------------------

class MembershipDocumentAPIView(generics.GenericAPIView):
    """
    Dedicated API for MembershipDocument with POST, GET, PUT operations
    """
    serializer_class = MembershipDocumentSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Create a new membership document - automatically determines membership from token
        """
        try:
            # Print request data to terminal
            print("\n" + "="*50)
            print("📤 MEMBERSHIP DOCUMENT POST REQUEST")
            print("="*50)
            print(f"🔗 URL: {request.get_full_path()}")
            print(f"🔐 User: {request.user}")
            print(f"📋 Method: {request.method}")
            print(f"📦 Content-Type: {request.content_type}")
            print("\n📊 REQUEST DATA:")
            print("-" * 30)

            # Print form data
            if hasattr(request, 'data'):
                for key, value in request.data.items():
                    if key == 'file' and hasattr(value, 'name'):
                        print(f"  {key}: {value.name} ({value.size} bytes)")
                    else:
                        print(f"  {key}: {value}")

            # Print files
            if hasattr(request, 'FILES') and request.FILES:
                print("\n📁 FILES:")
                print("-" * 30)
                for key, file in request.FILES.items():
                    print(
                        f"  {key}: {file.name} ({file.size} bytes, {file.content_type})")

            print("="*50)

            # Get user's registration and membership
            try:
                user_registration = Registration.objects.get(user=request.user)
                print(f"👤 User Registration ID: {user_registration.id}")

                # Get user's membership (assuming one membership per user for now)
                try:
                    user_membership = Membership.objects.get(
                        registration=user_registration)
                    print(f"🏢 User Membership ID: {user_membership.id}")
                    print(f"🏢 Company Name: {user_membership.company_name}")

                except Membership.DoesNotExist:
                    print("❌ User has no membership")
                    return Response({
                        "success": False,
                        "message": "No membership found. Please create a membership first.",
                    }, status=status.HTTP_404_NOT_FOUND)
                except Membership.MultipleObjectsReturned:
                    # If user has multiple memberships, get the first one
                    user_membership = Membership.objects.filter(
                        registration=user_registration).first()
                    print(
                        f"⚠️ Multiple memberships found, using first one: {user_membership.id}")

            except Registration.DoesNotExist:
                print("❌ User has no registration")
                return Response({
                    "success": False,
                    "message": "User registration not found. Please complete your registration first.",
                }, status=status.HTTP_404_NOT_FOUND)

            # Prepare data with automatically determined membership ID
            data = request.data.copy()
            data['membership'] = user_membership.id
            print(f"🔧 Auto-assigned membership ID: {user_membership.id}")

            serializer = MembershipDocumentSerializer(data=data)
            if serializer.is_valid():
                document = serializer.save()
                print(
                    f"✅ Document created successfully with ID: {document.id}")
                return Response({
                    "success": True,
                    "message": "Membership document created successfully!",
                    "data": serializer.data,
                    "auto_assigned_membership_id": user_membership.id,
                    "membership_company": user_membership.company_name
                }, status=status.HTTP_201_CREATED)
            else:
                print(f"❌ Validation errors: {serializer.errors}")
                return Response({
                    "success": False,
                    "message": "Please correct the errors below and try again.",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"💥 Server error: {str(e)}")
            return Response({
                "success": False,
                "message": "An unexpected error occurred. Please try again later.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, document_id=None):
        """
        Get a specific membership document by ID, or get all user's documents if no ID provided
        """
        try:
            # Print request info for debugging
            print("\n" + "="*50)
            print("📤 MEMBERSHIP DOCUMENT GET REQUEST")
            print("="*50)
            print(f"🔗 URL: {request.get_full_path()}")
            print(f"🔐 User: {request.user}")
            print(f"📋 Method: {request.method}")
            if document_id:
                print(f"🆔 Requested Document ID: {document_id}")
            print("="*50)

            # Get user's registration
            try:
                user_registration = Registration.objects.get(user=request.user)
                print(f"👤 User Registration ID: {user_registration.id}")

            except Registration.DoesNotExist:
                print("❌ User has no registration")
                return Response({
                    "success": False,
                    "message": "User registration not found. Please complete your registration first.",
                }, status=status.HTTP_404_NOT_FOUND)

            if document_id:
                # Get specific document and verify it belongs to user
                try:
                    document = MembershipDocument.objects.get(
                        pk=document_id,
                        membership__registration=user_registration
                    )
                    print(f"✅ Document {document_id} belongs to user")
                    serializer = MembershipDocumentSerializer(document)
                    return Response({
                        "success": True,
                        "data": serializer.data
                    }, status=status.HTTP_200_OK)
                except MembershipDocument.DoesNotExist:
                    print(
                        f"❌ Document {document_id} not found or doesn't belong to user")
                    return Response({
                        "success": False,
                        "message": "Membership document not found or you don't have permission to access it."
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                # Get all user's documents
                documents = MembershipDocument.objects.filter(
                    membership__registration=user_registration
                )
                print(f"📊 Found {documents.count()} documents for user")
                serializer = MembershipDocumentSerializer(documents, many=True)
                return Response({
                    "success": True,
                    "data": serializer.data,
                    "count": documents.count(),
                    "user_registration_id": user_registration.id
                }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"💥 Server error: {str(e)}")
            return Response({
                "success": False,
                "message": "Failed to retrieve membership document(s).",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, document_id):
        """
        Update a specific membership document
        """
        try:
            # Print request data to terminal
            print("\n" + "="*50)
            print("📤 MEMBERSHIP DOCUMENT PUT REQUEST")
            print("="*50)
            print(f"🔗 URL: {request.get_full_path()}")
            print(f"🔐 User: {request.user}")
            print(f"📋 Method: {request.method}")
            print(f"🆔 Requested Document ID: {document_id}")
            print(f"📦 Content-Type: {request.content_type}")
            print("\n📊 REQUEST DATA:")
            print("-" * 30)

            # Print form data
            if hasattr(request, 'data'):
                for key, value in request.data.items():
                    if key == 'file' and hasattr(value, 'name'):
                        print(f"  {key}: {value.name} ({value.size} bytes)")
                    else:
                        print(f"  {key}: {value}")

            # Print files
            if hasattr(request, 'FILES') and request.FILES:
                print("\n📁 FILES:")
                print("-" * 30)
                for key, file in request.FILES.items():
                    print(
                        f"  {key}: {file.name} ({file.size} bytes, {file.content_type})")

            print("="*50)

            # Get user's registration
            try:
                user_registration = Registration.objects.get(user=request.user)
                print(f"👤 User Registration ID: {user_registration.id}")

            except Registration.DoesNotExist:
                print("❌ User has no registration")
                return Response({
                    "success": False,
                    "message": "User registration not found. Please complete your registration first.",
                }, status=status.HTTP_404_NOT_FOUND)

            # Get document and verify it belongs to user
            try:
                document = MembershipDocument.objects.get(
                    pk=document_id,
                    membership__registration=user_registration
                )
                print(f"✅ Document {document_id} belongs to user")

            except MembershipDocument.DoesNotExist:
                print(
                    f"❌ Document {document_id} not found or doesn't belong to user")
                return Response({
                    "success": False,
                    "message": "Membership document not found or you don't have permission to update it."
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = MembershipDocumentSerializer(
                document, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                print(f"✅ Document {document_id} updated successfully")
                return Response({
                    "success": True,
                    "message": "Membership document updated successfully!",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)
            else:
                print(f"❌ Validation errors: {serializer.errors}")
                return Response({
                    "success": False,
                    "message": "Please correct the errors below and try again.",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(f"💥 Server error: {str(e)}")
            return Response({
                "success": False,
                "message": "An unexpected error occurred. Please try again later.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------------------------------------------------
# MEMBERSHIP PAYMENT API - Dedicated endpoints for membership payments
# ------------------------------------------------------------

class MembershipPaymentAPIView(generics.GenericAPIView):
    """
    Dedicated API for MembershipPayment with POST, GET, PUT operations
    """
    serializer_class = MembershipPaymentSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Create a new membership payment - automatically determines membership from token
        """
        try:
            # Print request data to terminal
            print("\n" + "="*50)
            print("📤 MEMBERSHIP PAYMENT POST REQUEST")
            print("="*50)
            print(f"🔗 URL: {request.get_full_path()}")
            print(f"🔐 User: {request.user}")
            print(f"📋 Method: {request.method}")
            print(f"📦 Content-Type: {request.content_type}")
            print("\n📊 REQUEST DATA:")
            print("-" * 30)

            # Print form data
            if hasattr(request, 'data'):
                for key, value in request.data.items():
                    if key == 'payment_proof' and hasattr(value, 'name'):
                        print(f"  {key}: {value.name} ({value.size} bytes)")
                    else:
                        print(f"  {key}: {value}")

            # Print files
            if hasattr(request, 'FILES') and request.FILES:
                print("\n📁 FILES:")
                print("-" * 30)
                for key, file in request.FILES.items():
                    print(
                        f"  {key}: {file.name} ({file.size} bytes, {file.content_type})")

            print("="*50)

            # Get user's registration and membership
            try:
                user_registration = Registration.objects.get(user=request.user)
                print(f"👤 User Registration ID: {user_registration.id}")

                # Get user's membership (assuming one membership per user for now)
                try:
                    user_membership = Membership.objects.get(
                        registration=user_registration)
                    print(f"🏢 User Membership ID: {user_membership.id}")
                    print(f"🏢 Company Name: {user_membership.company_name}")

                except Membership.DoesNotExist:
                    print("❌ User has no membership")
                    return Response({
                        "success": False,
                        "message": "No membership found. Please create a membership first.",
                    }, status=status.HTTP_404_NOT_FOUND)
                except Membership.MultipleObjectsReturned:
                    # If user has multiple memberships, get the first one
                    user_membership = Membership.objects.filter(
                        registration=user_registration).first()
                    print(
                        f"⚠️ Multiple memberships found, using first one: {user_membership.id}")

            except Registration.DoesNotExist:
                print("❌ User has no registration")
                return Response({
                    "success": False,
                    "message": "User registration not found. Please complete your registration first.",
                }, status=status.HTTP_404_NOT_FOUND)

            # Prepare data with automatically determined membership ID
            data = request.data.copy()
            data['membership'] = user_membership.id
            print(f"🔧 Auto-assigned membership ID: {user_membership.id}")

            serializer = MembershipPaymentSerializer(data=data)
            if serializer.is_valid():
                payment = serializer.save()
                print(f"✅ Payment created successfully with ID: {payment.id}")
                return Response({
                    "success": True,
                    "message": "Membership payment recorded successfully!",
                    "data": serializer.data,
                    "auto_assigned_membership_id": user_membership.id,
                    "membership_company": user_membership.company_name
                }, status=status.HTTP_201_CREATED)
            else:
                print(f"❌ Validation errors: {serializer.errors}")
                return Response({
                    "success": False,
                    "message": "Please correct the errors below and try again.",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"💥 Server error: {str(e)}")
            return Response({
                "success": False,
                "message": "An unexpected error occurred. Please try again later.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, payment_id=None):
        """
        Get a specific membership payment by ID, or get all user's payments if no ID provided
        """
        try:
            # Print request info for debugging
            print("\n" + "="*50)
            print("📤 MEMBERSHIP PAYMENT GET REQUEST")
            print("="*50)
            print(f"🔗 URL: {request.get_full_path()}")
            print(f"🔐 User: {request.user}")
            print(f"📋 Method: {request.method}")
            if payment_id:
                print(f"🆔 Requested Payment ID: {payment_id}")
            print("="*50)

            # Get user's registration
            try:
                user_registration = Registration.objects.get(user=request.user)
                print(f"👤 User Registration ID: {user_registration.id}")

            except Registration.DoesNotExist:
                print("❌ User has no registration")
                return Response({
                    "success": False,
                    "message": "User registration not found. Please complete your registration first.",
                }, status=status.HTTP_404_NOT_FOUND)

            if payment_id:
                # Get specific payment and verify it belongs to user
                try:
                    payment = MembershipPayment.objects.get(
                        pk=payment_id,
                        membership__registration=user_registration
                    )
                    print(f"✅ Payment {payment_id} belongs to user")
                    serializer = MembershipPaymentSerializer(payment)
                    return Response({
                        "success": True,
                        "data": serializer.data
                    }, status=status.HTTP_200_OK)
                except MembershipPayment.DoesNotExist:
                    print(
                        f"❌ Payment {payment_id} not found or doesn't belong to user")
                    return Response({
                        "success": False,
                        "message": "Membership payment not found or you don't have permission to access it."
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                # Get all user's payments
                payments = MembershipPayment.objects.filter(
                    membership__registration=user_registration
                )
                print(f"📊 Found {payments.count()} payments for user")
                serializer = MembershipPaymentSerializer(payments, many=True)
                return Response({
                    "success": True,
                    "data": serializer.data,
                    "count": payments.count(),
                    "user_registration_id": user_registration.id
                }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"💥 Server error: {str(e)}")
            return Response({
                "success": False,
                "message": "Failed to retrieve membership payment(s).",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, payment_id):
        """
        Update a specific membership payment
        """
        try:
            # Print request data to terminal
            print("\n" + "="*50)
            print("📤 MEMBERSHIP PAYMENT PUT REQUEST")
            print("="*50)
            print(f"🔗 URL: {request.get_full_path()}")
            print(f"🔐 User: {request.user}")
            print(f"📋 Method: {request.method}")
            print(f"🆔 Requested Payment ID: {payment_id}")
            print(f"📦 Content-Type: {request.content_type}")
            print("\n📊 REQUEST DATA:")
            print("-" * 30)

            # Print form data
            if hasattr(request, 'data'):
                for key, value in request.data.items():
                    if key == 'payment_proof' and hasattr(value, 'name'):
                        print(f"  {key}: {value.name} ({value.size} bytes)")
                    else:
                        print(f"  {key}: {value}")

            # Print files
            if hasattr(request, 'FILES') and request.FILES:
                print("\n📁 FILES:")
                print("-" * 30)
                for key, file in request.FILES.items():
                    print(
                        f"  {key}: {file.name} ({file.size} bytes, {file.content_type})")

            print("="*50)

            # Get user's registration
            try:
                user_registration = Registration.objects.get(user=request.user)
                print(f"👤 User Registration ID: {user_registration.id}")

            except Registration.DoesNotExist:
                print("❌ User has no registration")
                return Response({
                    "success": False,
                    "message": "User registration not found. Please complete your registration first.",
                }, status=status.HTTP_404_NOT_FOUND)

            # Get payment and verify it belongs to user
            try:
                payment = MembershipPayment.objects.get(
                    pk=payment_id,
                    membership__registration=user_registration
                )
                print(f"✅ Payment {payment_id} belongs to user")

            except MembershipPayment.DoesNotExist:
                print(
                    f"❌ Payment {payment_id} not found or doesn't belong to user")
                return Response({
                    "success": False,
                    "message": "Membership payment not found or you don't have permission to update it."
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = MembershipPaymentSerializer(
                payment, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                print(f"✅ Payment {payment_id} updated successfully")
                return Response({
                    "success": True,
                    "message": "Membership payment updated successfully!",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)
            else:
                print(f"❌ Validation errors: {serializer.errors}")
                return Response({
                    "success": False,
                    "message": "Please correct the errors below and try again.",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(f"💥 Server error: {str(e)}")
            return Response({
                "success": False,
                "message": "An unexpected error occurred. Please try again later.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MembershipPaymentByMembershipView(generics.GenericAPIView):
    """
    Get all membership payments for a specific membership
    """
    serializer_class = MembershipPaymentSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, membership_id):
        """
        Get all payments for a specific membership (user's own membership only)
        """
        try:
            # Print request info for debugging
            print("\n" + "="*50)
            print("📤 MEMBERSHIP PAYMENTS BY MEMBERSHIP GET REQUEST")
            print("="*50)
            print(f"🔗 URL: {request.get_full_path()}")
            print(f"🔐 User: {request.user}")
            print(f"📋 Method: {request.method}")
            print(f"🆔 Requested Membership ID: {membership_id}")
            print("="*50)

            # Get user's registration
            try:
                user_registration = Registration.objects.get(user=request.user)
                print(f"👤 User Registration ID: {user_registration.id}")

            except Registration.DoesNotExist:
                print("❌ User has no registration")
                return Response({
                    "success": False,
                    "message": "User registration not found. Please complete your registration first.",
                }, status=status.HTTP_404_NOT_FOUND)

            # Get membership and verify it belongs to user
            try:
                membership = Membership.objects.get(
                    pk=membership_id,
                    registration=user_registration
                )
                print(f"✅ Membership {membership_id} belongs to user")

            except Membership.DoesNotExist:
                print(
                    f"❌ Membership {membership_id} not found or doesn't belong to user")
                return Response({
                    "success": False,
                    "message": "Membership not found or you don't have permission to access it."
                }, status=status.HTTP_404_NOT_FOUND)

            # Get payments for this membership
            payments = MembershipPayment.objects.filter(membership=membership)
            print(
                f"📊 Found {payments.count()} payments for membership {membership_id}")

            serializer = MembershipPaymentSerializer(payments, many=True)
            return Response({
                "success": True,
                "data": serializer.data,
                "count": payments.count(),
                "membership_id": membership_id,
                "membership_company": membership.company_name,
                "user_registration_id": user_registration.id
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"💥 Server error: {str(e)}")
            return Response({
                "success": False,
                "message": "Failed to retrieve membership payments.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------------------------------------------------
# QUOTATION API - Dedicated endpoints for quotations
# ------------------------------------------------------------

class QuotationAPIView(generics.GenericAPIView):
    """
    Dedicated API for Quotation with POST, GET operations
    """
    serializer_class = QuotationSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Create a new quotation - automatically determines membership from token
        """
        try:
            # Print request data to terminal
            print("\n" + "="*50)
            print("📤 QUOTATION POST REQUEST")
            print("="*50)
            print(f"🔗 URL: {request.get_full_path()}")
            print(f"🔐 User: {request.user}")
            print(f"📋 Method: {request.method}")
            print(f"📦 Content-Type: {request.content_type}")
            print("\n📊 REQUEST DATA:")
            print("-" * 30)

            # Print form data
            if hasattr(request, 'data'):
                for key, value in request.data.items():
                    if key == 'guideline_files' and isinstance(value, list):
                        print(f"  {key}: {len(value)} files")
                        for i, file_data in enumerate(value):
                            if isinstance(file_data, dict):
                                print(
                                    f"    File {i+1}: {file_data.get('file_name', 'No name')} - {type(file_data.get('file', 'No file'))}")
                            else:
                                print(f"    File {i+1}: {type(value)}")
                    elif key == 'items' and isinstance(value, list):
                        print(f"  {key}: {len(value)} items")
                        for i, item in enumerate(value):
                            if isinstance(item, dict):
                                print(
                                    f"    Item {i+1}: Product {item.get('product', 'N/A')} - ₹{item.get('quoted_price', 'N/A')}")
                    else:
                        print(f"  {key}: {value}")

            print("="*50)

            # Get user's registration and membership
            try:
                user_registration = Registration.objects.get(user=request.user)
                print(f"👤 User Registration ID: {user_registration.id}")

                # Get user's membership (assuming one membership per user for now)
                try:
                    user_membership = Membership.objects.get(
                        registration=user_registration)
                    print(f"🏢 User Membership ID: {user_membership.id}")
                    print(f"🏢 Company Name: {user_membership.company_name}")

                except Membership.DoesNotExist:
                    print("❌ User has no membership")
                    return Response({
                        "success": False,
                        "message": "No membership found. Please create a membership first.",
                    }, status=status.HTTP_404_NOT_FOUND)
                except Membership.MultipleObjectsReturned:
                    # If user has multiple memberships, get the first one
                    user_membership = Membership.objects.filter(
                        registration=user_registration).first()
                    print(
                        f"⚠️ Multiple memberships found, using first one: {user_membership.id}")

            except Registration.DoesNotExist:
                print("❌ User has no registration")
                return Response({
                    "success": False,
                    "message": "User registration not found. Please complete your registration first.",
                }, status=status.HTTP_404_NOT_FOUND)

            # Prepare data with automatically determined membership ID
            data = request.data.copy()
            data['membership'] = user_membership.id
            print(f"🔧 Auto-assigned membership ID: {user_membership.id}")

            serializer = QuotationSerializer(data=data)
            if serializer.is_valid():
                try:
                    quotation = serializer.save()
                    print(
                        f"✅ Quotation created successfully with ID: {quotation.id}")
                    print(f"📦 Items created: {quotation.items.count()}")
                    print(
                        f"📁 Files uploaded: {quotation.guideline_files.count()}")
                    return Response({
                        "success": True,
                        "message": "Quotation created successfully with all items and files!",
                        "data": QuotationSerializer(quotation).data,
                        "auto_assigned_membership_id": user_membership.id,
                        "membership_company": user_membership.company_name,
                        "items_count": quotation.items.count(),
                        "files_count": quotation.guideline_files.count()
                    }, status=status.HTTP_201_CREATED)
                except Exception as e:
                    print(f"💥 Transaction failed: {str(e)}")
                    return Response({
                        "success": False,
                        "message": "Failed to create quotation. All changes have been rolled back.",
                        "error": str(e)
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                print(f"❌ Validation errors: {serializer.errors}")
                return Response({
                    "success": False,
                    "message": "Please correct the errors below and try again.",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"💥 Server error: {str(e)}")
            return Response({
                "success": False,
                "message": "An unexpected error occurred. Please try again later.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, quotation_id=None):
        """
        Get a specific quotation by ID, or get all user's quotations if no ID provided
        """
        try:
            # Print request info for debugging
            print("\n" + "="*50)
            print("📤 QUOTATION GET REQUEST")
            print("="*50)
            print(f"🔗 URL: {request.get_full_path()}")
            print(f"🔐 User: {request.user}")
            print(f"📋 Method: {request.method}")
            if quotation_id:
                print(f"🆔 Requested Quotation ID: {quotation_id}")
            print("="*50)

            # Get user's registration
            try:
                user_registration = Registration.objects.get(user=request.user)
                print(f"👤 User Registration ID: {user_registration.id}")

            except Registration.DoesNotExist:
                print("❌ User has no registration")
                return Response({
                    "success": False,
                    "message": "User registration not found. Please complete your registration first.",
                }, status=status.HTTP_404_NOT_FOUND)

            if quotation_id:
                # Get specific quotation and verify it belongs to user
                try:
                    quotation = Quotation.objects.get(
                        pk=quotation_id,
                        membership__registration=user_registration
                    )
                    print(f"✅ Quotation {quotation_id} belongs to user")
                    serializer = QuotationSerializer(quotation)
                    return Response({
                        "success": True,
                        "data": serializer.data
                    }, status=status.HTTP_200_OK)
                except Quotation.DoesNotExist:
                    print(
                        f"❌ Quotation {quotation_id} not found or doesn't belong to user")
                    return Response({
                        "success": False,
                        "message": "Quotation not found or you don't have permission to access it."
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                # Get all user's quotations
                quotations = Quotation.objects.filter(
                    membership__registration=user_registration
                )
                print(f"📊 Found {quotations.count()} quotations for user")
                serializer = QuotationSerializer(quotations, many=True)
                return Response({
                    "success": True,
                    "data": serializer.data,
                    "count": quotations.count(),
                    "user_registration_id": user_registration.id
                }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"💥 Server error: {str(e)}")
            return Response({
                "success": False,
                "message": "Failed to retrieve quotation(s).",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class QuotationByMembershipView(generics.GenericAPIView):
    """
    Get all quotations for a specific membership
    """
    serializer_class = QuotationSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, membership_id):
        """
        Get all quotations for a specific membership (user's own membership only)
        """
        try:
            # Print request info for debugging
            print("\n" + "="*50)
            print("📤 QUOTATIONS BY MEMBERSHIP GET REQUEST")
            print("="*50)
            print(f"🔗 URL: {request.get_full_path()}")
            print(f"🔐 User: {request.user}")
            print(f"📋 Method: {request.method}")
            print(f"🆔 Requested Membership ID: {membership_id}")
            print("="*50)

            # Get user's registration
            try:
                user_registration = Registration.objects.get(user=request.user)
                print(f"👤 User Registration ID: {user_registration.id}")

            except Registration.DoesNotExist:
                print("❌ User has no registration")
                return Response({
                    "success": False,
                    "message": "User registration not found. Please complete your registration first.",
                }, status=status.HTTP_404_NOT_FOUND)

            # Get membership and verify it belongs to user
            try:
                membership = Membership.objects.get(
                    pk=membership_id,
                    registration=user_registration
                )
                print(f"✅ Membership {membership_id} belongs to user")

            except Membership.DoesNotExist:
                print(
                    f"❌ Membership {membership_id} not found or doesn't belong to user")
                return Response({
                    "success": False,
                    "message": "Membership not found or you don't have permission to access it."
                }, status=status.HTTP_404_NOT_FOUND)

            # Get quotations for this membership
            quotations = Quotation.objects.filter(membership=membership)
            print(
                f"📊 Found {quotations.count()} quotations for membership {membership_id}")

            serializer = QuotationSerializer(quotations, many=True)
            return Response({
                "success": True,
                "data": serializer.data,
                "count": quotations.count(),
                "membership_id": membership_id,
                "membership_company": membership.company_name,
                "user_registration_id": user_registration.id
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"💥 Server error: {str(e)}")
            return Response({
                "success": False,
                "message": "Failed to retrieve quotations.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MembershipDocumentByMembershipView(generics.GenericAPIView):
    """
    Get all membership documents for a specific membership
    """
    serializer_class = MembershipDocumentSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, membership_id):
        """
        Get all documents for a specific membership (user's own membership only)
        """
        try:
            # Print request info for debugging
            print("\n" + "="*50)
            print("📤 MEMBERSHIP DOCUMENTS BY MEMBERSHIP GET REQUEST")
            print("="*50)
            print(f"🔗 URL: {request.get_full_path()}")
            print(f"🔐 User: {request.user}")
            print(f"📋 Method: {request.method}")
            print(f"🆔 Requested Membership ID: {membership_id}")
            print("="*50)

            # Get user's registration
            try:
                user_registration = Registration.objects.get(user=request.user)
                print(f"👤 User Registration ID: {user_registration.id}")

            except Registration.DoesNotExist:
                print("❌ User has no registration")
                return Response({
                    "success": False,
                    "message": "User registration not found. Please complete your registration first.",
                }, status=status.HTTP_404_NOT_FOUND)

            # Get membership and verify it belongs to user
            try:
                membership = Membership.objects.get(
                    pk=membership_id,
                    registration=user_registration
                )
                print(f"✅ Membership {membership_id} belongs to user")

            except Membership.DoesNotExist:
                print(
                    f"❌ Membership {membership_id} not found or doesn't belong to user")
                return Response({
                    "success": False,
                    "message": "Membership not found or you don't have permission to access it."
                }, status=status.HTTP_404_NOT_FOUND)

            # Get documents for this membership
            documents = MembershipDocument.objects.filter(
                membership=membership)
            print(
                f"📊 Found {documents.count()} documents for membership {membership_id}")

            serializer = MembershipDocumentSerializer(documents, many=True)
            return Response({
                "success": True,
                "data": serializer.data,
                "count": documents.count(),
                "membership_id": membership_id,
                "membership_company": membership.company_name,
                "user_registration_id": user_registration.id
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"💥 Server error: {str(e)}")
            return Response({
                "success": False,
                "message": "Failed to retrieve membership documents.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
