from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .models import Registration, Product, ProductDocument, ProductRegistration, Membership, MembershipDocument, MembershipPayment, Quotation, QuotationItem, QuotationGuidelineFile


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
            "institution_name", "is_verified", "created_at", "updated_at",
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


class MembershipDocumentSerializer(serializers.ModelSerializer):
    # Add human-readable field names
    document_type_display = serializers.CharField(
        source='get_document_type_display', read_only=True)
    verification_status_display = serializers.CharField(
        source='get_verification_status_display', read_only=True)
    verified_by_username = serializers.CharField(
        source='verified_by.username', read_only=True)

    class Meta:
        model = MembershipDocument
        fields = [
            'id', 'membership', 'document_type', 'document_type_display', 'document_name', 'file',
            'uploaded_at', 'remarks', 'verification_status', 'verification_status_display',
            'verified_at', 'verified_by', 'verified_by_username', 'verification_remarks'
        ]
        read_only_fields = [
            'uploaded_at', 'document_type_display', 'verification_status_display',
            'verified_at', 'verified_by', 'verified_by_username', 'verification_remarks'
        ]
        extra_kwargs = {
            'membership': {
                'error_messages': {
                    'required': 'Please select a membership is required',
                    'invalid': 'Please select a valid membership'
                }
            },
            'document_type': {
                'error_messages': {
                    'required': 'Please select a document type',
                    'invalid_choice': 'Please select a valid document type from the list',
                    'blank': 'Document type cannot be empty'
                }
            },
            'document_name': {
                'error_messages': {
                    'required': 'Please provide a name for this document',
                    'blank': 'Document name cannot be empty',
                    'max_length': 'Document name is too long (maximum 255 characters)'
                }
            },
            'file': {
                'error_messages': {
                    'required': 'Please select a file to upload',
                    'invalid': 'Please select a valid file',
                    'empty': 'The selected file is empty'
                }
            },
            'remarks': {
                'error_messages': {
                    'max_length': 'Remarks are too long (please keep under 1000 characters)'
                }
            }
        }

    def validate_membership(self, value):
        """Validate that the membership exists and is accessible"""
        if not value:
            raise serializers.ValidationError("Please select a membership.")

        try:
            membership = Membership.objects.get(
                pk=value.id if hasattr(value, 'id') else value)
            return membership
        except Membership.DoesNotExist:
            raise serializers.ValidationError(
                "The selected membership does not exist.")
        except Exception:
            raise serializers.ValidationError("Invalid membership selection.")

    def validate_document_type(self, value):
        """Validate document type with friendly messages"""
        if not value:
            raise serializers.ValidationError("Please select a document type.")

        valid_types = [choice[0]
                       for choice in MembershipDocument.DOCUMENT_TYPES]
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Please select a valid document type. Available options: {', '.join(valid_types)}"
            )
        return value

    def validate_document_name(self, value):
        """Validate document name with friendly messages"""
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Please provide a meaningful name for this document.")

        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Document name should be at least 3 characters long.")

        if len(value) > 255:
            raise serializers.ValidationError(
                "Document name is too long. Please keep it under 255 characters.")

        return value.strip()

    def validate_file(self, value):
        """Validate file upload with friendly messages"""
        if not value:
            raise serializers.ValidationError(
                "Please select a file to upload.")

        # Check file size (limit to 10MB)
        if hasattr(value, 'size') and value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError(
                "File is too large. Please select a file smaller than 10MB."
            )

        # Check file type (basic validation)
        if hasattr(value, 'name'):
            allowed_extensions = ['.pdf', '.doc',
                                  '.docx', '.jpg', '.jpeg', '.png', '.gif']
            file_extension = '.' + value.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                raise serializers.ValidationError(
                    f"File type not supported. Please upload one of: {', '.join(allowed_extensions)}"
                )

        return value

    def validate_remarks(self, value):
        """Validate remarks with friendly messages"""
        if value and len(value) > 1000:
            raise serializers.ValidationError(
                "Remarks are too long. Please keep them under 1000 characters."
            )
        return value

    def validate(self, attrs):
        """Cross-field validation with friendly messages"""
        membership = attrs.get('membership')
        document_type = attrs.get('document_type')

        # Check if user already has this document type for this membership
        if membership and document_type:
            existing_doc = MembershipDocument.objects.filter(
                membership=membership,
                document_type=document_type
            ).exclude(id=self.instance.id if self.instance else None)

            if existing_doc.exists():
                doc_type_display = dict(MembershipDocument.DOCUMENT_TYPES).get(
                    document_type, document_type)
                raise serializers.ValidationError(
                    f"You have already uploaded a {doc_type_display} for this membership. "
                    f"Please update the existing document instead of creating a new one."
                )

        return attrs


class MembershipPaymentSerializer(serializers.ModelSerializer):
    # Add human-readable field names
    method_display = serializers.CharField(
        source='get_method_display', read_only=True)
    status_display = serializers.CharField(
        source='get_status_display', read_only=True)
    currency_display = serializers.CharField(
        source='get_currency_display', read_only=True)
    verification_status_display = serializers.CharField(
        source='get_verification_status_display', read_only=True)
    verified_by_username = serializers.CharField(
        source='verified_by.username', read_only=True)

    class Meta:
        model = MembershipPayment
        fields = [
            'id', 'membership', 'payment_proof', 'payment_date', 'payment_reference',
            'amount', 'currency', 'currency_display', 'method', 'method_display',
            'status', 'status_display', 'verification_status', 'verification_status_display',
            'verified_at', 'verified_by', 'verified_by_username', 'verification_remarks',
            'remarks', 'created_at'
        ]
        read_only_fields = [
            'payment_date', 'created_at', 'method_display', 'status_display', 'currency_display',
            'verification_status_display', 'verified_at', 'verified_by', 'verified_by_username', 'verification_remarks'
        ]
        extra_kwargs = {
            'membership': {
                'error_messages': {
                    'required': 'Please select a membership',
                    'invalid': 'Please select a valid membership'
                }
            },
            'amount': {
                'error_messages': {
                    'required': 'Please enter the payment amount',
                    'invalid': 'Please enter a valid amount',
                    'max_digits': 'Amount is too large. Please enter a smaller amount.',
                    'max_decimal_places': 'Amount can have at most 2 decimal places.'
                }
            },
            'currency': {
                'error_messages': {
                    'required': 'Please select a currency',
                    'invalid_choice': 'Please select a valid currency from the list'
                }
            },
            'method': {
                'error_messages': {
                    'required': 'Please select a payment method',
                    'invalid_choice': 'Please select a valid payment method from the list'
                }
            },
            'payment_reference': {
                'error_messages': {
                    'max_length': 'Payment reference is too long. Please keep it under 100 characters.'
                }
            },
            'remarks': {
                'error_messages': {
                    'max_length': 'Remarks are too long. Please keep them under 1000 characters.'
                }
            }
        }

    def validate_amount(self, value):
        """Validate payment amount with friendly messages"""
        if value is None:
            raise serializers.ValidationError(
                "Please enter the payment amount.")

        if value <= 0:
            raise serializers.ValidationError(
                "Payment amount must be greater than zero.")

        if value > 999999999.99:
            raise serializers.ValidationError(
                "Payment amount is too large. Please enter an amount less than 1 billion."
            )

        return value

    def validate_currency(self, value):
        """Validate currency with friendly messages"""
        if not value:
            raise serializers.ValidationError("Please select a currency.")

        valid_currencies = [choice[0]
                            for choice in MembershipPayment.CURRENCY_CHOICES]
        if value not in valid_currencies:
            raise serializers.ValidationError(
                f"Please select a valid currency. Available options: {', '.join(valid_currencies)}"
            )

        return value

    def validate_method(self, value):
        """Validate payment method with friendly messages"""
        if not value:
            raise serializers.ValidationError(
                "Please select a payment method.")

        valid_methods = [choice[0]
                         for choice in MembershipPayment.PAYMENT_METHOD_CHOICES]
        if value not in valid_methods:
            raise serializers.ValidationError(
                f"Please select a valid payment method. Available options: {', '.join(valid_methods)}"
            )

        return value

    def validate_payment_reference(self, value):
        """Validate payment reference with friendly messages"""
        if value and len(value) > 100:
            raise serializers.ValidationError(
                "Payment reference is too long. Please keep it under 100 characters."
            )

        return value

    def validate_remarks(self, value):
        """Validate remarks with friendly messages"""
        if value and len(value) > 1000:
            raise serializers.ValidationError(
                "Remarks are too long. Please keep them under 1000 characters."
            )

        return value

    def validate_payment_proof(self, value):
        """Validate payment proof file with friendly messages"""
        if value:
            # Check file size (limit to 10MB)
            if hasattr(value, 'size') and value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError(
                    "Payment proof file is too large. Please select a file smaller than 10MB."
                )

            # Check file type
            if hasattr(value, 'name'):
                allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif']
                file_extension = '.' + value.name.split('.')[-1].lower()
                if file_extension not in allowed_extensions:
                    raise serializers.ValidationError(
                        f"File type not supported. Please upload one of: {', '.join(allowed_extensions)}"
                    )

        return value

    def validate(self, attrs):
        """Cross-field validation with friendly messages"""
        membership = attrs.get('membership')
        amount = attrs.get('amount')
        currency = attrs.get('currency')

        # Validate amount based on currency
        if amount and currency:
            if currency == 'INR' and amount > 10000000:  # 1 crore INR
                raise serializers.ValidationError(
                    "Amount is too large for INR. Please enter an amount less than 1 crore INR."
                )
            elif currency == 'USD' and amount > 100000:  # 100k USD
                raise serializers.ValidationError(
                    "Amount is too large for USD. Please enter an amount less than 100,000 USD."
                )

        return attrs


# ------------------------------------------------------------
# QUOTATION SERIALIZERS
# ------------------------------------------------------------

class QuotationGuidelineFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuotationGuidelineFile
        fields = [
            'id', 'quotation', 'file_name', 'file', 'uploaded_at'
        ]
        read_only_fields = ['uploaded_at']
        extra_kwargs = {
            'file': {
                'required': False,  # File is now optional
                'allow_null': True,
                'error_messages': {
                    'invalid': 'Please select a valid file'
                }
            },
            'file_name': {
                'required': False,
                'allow_blank': True,
                'error_messages': {
                    'max_length': 'File name is too long. Please keep it under 255 characters.'
                }
            }
        }

    def validate_file(self, value):
        """Validate file upload with friendly messages"""
        # File is now optional, so only validate if provided
        if value:
            # Check file size (limit to 10MB)
            if hasattr(value, 'size') and value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError(
                    "File is too large. Please select a file smaller than 10MB."
                )

            # Check file type
            if hasattr(value, 'name'):
                allowed_extensions = ['.pdf', '.doc',
                                      '.docx', '.jpg', '.jpeg', '.png', '.gif']
                file_extension = '.' + value.name.split('.')[-1].lower()
                if file_extension not in allowed_extensions:
                    raise serializers.ValidationError(
                        f"File type not supported. Please upload one of: {', '.join(allowed_extensions)}"
                    )

        return value

    def validate(self, attrs):
        """Cross-field validation"""
        file = attrs.get('file')
        file_name = attrs.get('file_name')

        # If file is provided but no file_name, use the original filename
        if file and not file_name:
            if hasattr(file, 'name'):
                attrs['file_name'] = file.name

        # If file_name is provided but no file, that's okay (file can be added later)
        if file_name and not file:
            # This is allowed - file can be uploaded separately
            pass

        return attrs


class QuotationItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        source='product.product_name', read_only=True)
    product_category = serializers.CharField(
        source='product.category', read_only=True)
    quoted_by_username = serializers.CharField(
        source='quoted_by.username', read_only=True)

    class Meta:
        model = QuotationItem
        fields = [
            'id', 'quotation', 'product', 'product_name', 'product_category',
            'currency', 'quoted_price', 'quoted_by', 'quoted_by_username', 'remarks'
        ]
        read_only_fields = ['quoted_by_username']
        extra_kwargs = {
            'quotation': {
                'required': False,  # Not required when used as nested serializer
                'write_only': True  # Don't include in response when nested
            },
            'quoted_price': {
                'required': True,  # Make quoted_price required
                'error_messages': {
                    'required': 'Please enter the quoted price',
                    'invalid': 'Please enter a valid price',
                    'max_digits': 'Price is too large. Please enter a smaller amount.',
                    'max_decimal_places': 'Price can have at most 2 decimal places.'
                }
            },
            'currency': {
                'error_messages': {
                    'invalid_choice': 'Please select a valid currency from the list'
                }
            }
        }

    def validate_quoted_price(self, value):
        """Validate quoted price with friendly messages"""
        if value is not None and value <= 0:
            raise serializers.ValidationError(
                "Quoted price must be greater than zero.")

        if value and value > 999999999.99:
            raise serializers.ValidationError(
                "Quoted price is too large. Please enter a price less than 1 billion."
            )

        return value

    def validate_currency(self, value):
        """Validate currency with friendly messages"""
        if value:
            valid_currencies = [choice[0]
                                for choice in QuotationItem.CURRENCY_CHOICES]
            if value not in valid_currencies:
                raise serializers.ValidationError(
                    f"Please select a valid currency. Available options: {', '.join(valid_currencies)}"
                )

        return value


class QuotationSerializer(serializers.ModelSerializer):
    # Add human-readable field names
    status_display = serializers.CharField(
        source='get_status_display', read_only=True)
    currency_display = serializers.CharField(
        source='get_currency_display', read_only=True)
    membership_company = serializers.CharField(
        source='membership.company_name', read_only=True)

    # Nested serializers for atomic operations
    items = QuotationItemSerializer(many=True, required=False)
    guideline_files = QuotationGuidelineFileSerializer(
        many=True, required=False)

    class Meta:
        model = Quotation
        fields = [
            'id', 'membership', 'membership_company', 'country', 'currency', 'currency_display',
            'title', 'description', 'authority_department', 'authority_website',
            'authority_contact_details', 'status', 'status_display', 'created_at',
            'updated_at', 'items', 'guideline_files'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'status_display', 'currency_display',
            'membership_company'
        ]
        extra_kwargs = {
            'membership': {
                'error_messages': {
                    'required': 'Please select a membership',
                    'invalid': 'Please select a valid membership'
                }
            },
            'country': {
                'error_messages': {
                    'required': 'Please enter the country',
                    'max_length': 'Country name is too long. Please keep it under 100 characters.'
                }
            },
            'currency': {
                'error_messages': {
                    'required': 'Please select a currency',
                    'invalid_choice': 'Please select a valid currency from the list'
                }
            },
            'title': {
                'error_messages': {
                    'required': 'Please enter a title for the quotation',
                    'max_length': 'Title is too long. Please keep it under 255 characters.'
                }
            },
            'authority_department': {
                'error_messages': {
                    'max_length': 'Department name is too long. Please keep it under 255 characters.'
                }
            },
            'authority_website': {
                'error_messages': {
                    'invalid': 'Please enter a valid website URL'
                }
            }
        }

    def validate_country(self, value):
        """Validate country with friendly messages"""
        if not value or not value.strip():
            raise serializers.ValidationError("Please enter the country name.")

        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Country name should be at least 2 characters long.")

        return value.strip()

    def validate_currency(self, value):
        """Validate currency with friendly messages"""
        if not value:
            raise serializers.ValidationError("Please select a currency.")

        valid_currencies = [choice[0] for choice in Quotation.CURRENCY_CHOICES]
        if value not in valid_currencies:
            raise serializers.ValidationError(
                f"Please select a valid currency. Available options: {', '.join(valid_currencies)}"
            )

        return value

    def validate_title(self, value):
        """Validate title with friendly messages"""
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Please enter a title for the quotation.")

        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Title should be at least 3 characters long.")

        return value.strip()

    def validate_authority_website(self, value):
        """Validate website URL with friendly messages"""
        if value and not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError(
                "Please enter a valid website URL starting with http:// or https://")

        return value

    def create(self, validated_data):
        """Create quotation with atomic transaction for items and files"""
        from django.db import transaction

        # Extract nested data
        items_data = validated_data.pop('items', [])
        guideline_files_data = validated_data.pop('guideline_files', [])

        with transaction.atomic():
            # Create the quotation
            quotation = Quotation.objects.create(**validated_data)

            # Create quotation items
            for item_data in items_data:
                QuotationItem.objects.create(quotation=quotation, **item_data)

            # Create guideline files
            for file_data in guideline_files_data:
                QuotationGuidelineFile.objects.create(
                    quotation=quotation, **file_data)

            return quotation

    def update(self, instance, validated_data):
        """Update quotation with atomic transaction for items and files"""
        from django.db import transaction

        # Extract nested data
        items_data = validated_data.pop('items', [])
        guideline_files_data = validated_data.pop('guideline_files', [])

        with transaction.atomic():
            # Update the quotation
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            # Update quotation items (delete existing and create new ones)
            if items_data is not None:
                instance.items.all().delete()
                for item_data in items_data:
                    QuotationItem.objects.create(
                        quotation=instance, **item_data)

            # Update guideline files (delete existing and create new ones)
            if guideline_files_data is not None:
                instance.guideline_files.all().delete()
                for file_data in guideline_files_data:
                    QuotationGuidelineFile.objects.create(
                        quotation=instance, **file_data)

            return instance


class MembershipSerializer(serializers.ModelSerializer):
    documents = MembershipDocumentSerializer(many=True, read_only=True)
    payments = MembershipPaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Membership
        fields = [
            'id', 'registration', 'company_name', 'email', 'phone',
            'country', 'state', 'district', 'city', 'address', 'pincode',
            'membership_type', 'payment_status', 'membership_status', 'start_date',
            'end_date', 'remarks', 'created_at', 'updated_at', 'documents', 'payments'
        ]
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'company_name': {'error_messages': {'required': 'Company name is required'}},
            'email': {'error_messages': {'required': 'Email is required', 'invalid': 'Please enter a valid email address'}},
            'phone': {'error_messages': {'required': 'Phone number is required'}},
            'country': {'error_messages': {'required': 'Country is required'}},
            'state': {'error_messages': {'required': 'State is required'}},
            'city': {'error_messages': {'required': 'City is required'}},
            'pincode': {'error_messages': {'required': 'Pincode is required'}},
            # Optional fields - no error messages needed
            'district': {'required': False},
            'address': {'required': False},
            'payment_status': {'required': False},
            'membership_status': {'required': False},
            'start_date': {'required': False},
            'end_date': {'required': False},
            'remarks': {'required': False},
        }

    def validate_email(self, value):
        if Membership.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "This email is already registered for membership.")
        return value

    def validate_phone(self, value):
        if not value.isdigit() or len(value) < 10:
            raise serializers.ValidationError(
                "Please enter a valid phone number with at least 10 digits.")
        return value
