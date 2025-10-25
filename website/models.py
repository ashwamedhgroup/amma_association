from django.db import models
from django.contrib.auth.models import User

# Create your models here.
'''

class HeroImage(models.Model):
    image = models.ImageField(upload_to="hero_images/")
    caption = models.CharField(max_length=255)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.caption


class Event(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to="event_images/")
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Notice(models.Model):
    CATEGORY_CHOICES = (
        ("notice", "Notice"),
        ("event", "Event"),
        ("update", "Update"),
        ("circular", "Circular"),
    )
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to="notice_images/")
    date = models.DateField()
    venue = models.CharField(max_length=255)
    category = models.CharField(max_length=255, choices=CATEGORY_CHOICES)
    description = models.TextField()
    objectives = models.TextField()
    registration_link = models.URLField(blank=True, null=True)
    registration_fee = models.TextField(blank=True, null=True)
    bank_details = models.TextField(blank=True, null=True)
    contact_person = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

'''
# ------------------------------------------------------------
# 1️⃣ REGISTRATION – Basic company / user profile
# ------------------------------------------------------------


class Registration(models.Model):
    USER_TYPES = (
        ("company", "Company"),
        ("ngo", "NGO"),
        ("university", "University"),
        ("researcher", "Researcher"),
        ("other", "Other"),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=50, choices=USER_TYPES)
    contact_number = models.CharField(max_length=20)
    institution_name = models.CharField(max_length=255, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    district = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    website = models.URLField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.user_type})"


class Product(models.Model):
    CATEGORY_CHOICES = (
        ("biofertilizer", "Biofertilizer"),
        ("biopesticide", "Biopesticide"),
        ("biostimulant", "Biostimulant"),
        ("biocontrol", "Biocontrol"),
    )

    FORMULATION_CHOICES = (
        ("aqueous_suspension", "Aqueous Suspension"),
        ("wettable_powder", "Wettable Powder"),
        ("emulsion", "Emulsion"),
        ("suspension", "Suspension"),
    )

    product_name = models.CharField(max_length=255)
    biocontrol_agent_name = models.CharField(max_length=255)
    biocontrol_agent_strain = models.CharField(max_length=255)
    accession_number = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=255, choices=CATEGORY_CHOICES)
    cfu = models.CharField(max_length=255, blank=True, null=True)
    formulation = models.CharField(max_length=255, choices=FORMULATION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product_name} ({self.category})"


class ProductRegistration(models.Model):
    REGISTRATION_STATUS_CHOICES = (
        ("registered", "Registered"),
        ("pending", "Pending"),
        ("rejected", "Rejected"),
    )

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="registrations"
    )
    country = models.CharField(max_length=100)
    registration_status = models.CharField(
        max_length=50, choices=REGISTRATION_STATUS_CHOICES, default="pending"
    )
    registration_number = models.CharField(
        max_length=255, blank=True, null=True)
    registration_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ("product", "country")

    def __str__(self):
        return f"{self.product.product_name} - {self.country}"


class ProductDocument(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="documents")
    document_name = models.CharField(max_length=255)
    file = models.FileField(upload_to="product_docs/", blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.document_name} ({self.product.product_name})"


class Membership(models.Model):
    MEMBERSHIP_TYPES = (
        ("data", "Data Membership"),
    )

    PAYMENT_STATUS_CHOICES = (
        ("pending", "Pending"),
        ("partially_paid", "Partially Paid"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    )

    MEMBERSHIP_STATUS_CHOICES = (
        ("inactive", "Inactive"),
        ("active", "Active"),
    )

    registration = models.ForeignKey(
        "Registration", on_delete=models.CASCADE, related_name="memberships"
    )
    company_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    district = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100)
    address = models.TextField(blank=True, null=True)

    pincode = models.CharField(max_length=10)

    membership_type = models.CharField(
        max_length=50, choices=MEMBERSHIP_TYPES, default="data"
    )
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending"
    )
    membership_status = models.CharField(
        max_length=20, choices=MEMBERSHIP_STATUS_CHOICES, default="inactive"
    )

    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company_name} - {self.membership_type}"


class MembershipDocument(models.Model):
    DOCUMENT_VERIFICATION_STATUS_CHOICES = (
        ("pending", "Pending"),
        ("verified", "Verified"),
        ("rejected", "Rejected"),
    )
    DOCUMENT_TYPES = (
        # 1️⃣ Entity Proof
        ("certificate_of_incorporation", "Certificate of Incorporation"),
        ("tax_registration_certificate", "Tax / VAT / GST Certificate"),

        # 2️⃣ Identity & Authorization
        ("government_id_proof", "Government / National ID or Passport"),
        ("authorized_signatory_letter",
         "Authorized Signatory / Board Authorization Letter"),

        # 3️⃣ Address & Banking
        ("registered_address_proof", "Registered / Operational Address Proof"),
        ("bank_account_proof", "Bank Account Proof (Cheque / Statement)"),
    )

    membership = models.ForeignKey(
        Membership, on_delete=models.CASCADE, related_name="documents"
    )
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    document_name = models.CharField(max_length=255)
    file = models.FileField(upload_to="membership_documents/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, null=True)
    verification_status = models.CharField(
        max_length=20, choices=DOCUMENT_VERIFICATION_STATUS_CHOICES, default="pending")
    verified_at = models.DateTimeField(blank=True, null=True)
    verified_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True)
    verification_remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.membership.company_name} - {self.document_type}"


class MembershipPayment(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ("bank_transfer", "Bank Transfer"),
        ("upi", "UPI"),
        ("paypal", "PayPal"),
        ("cash", "Cash"),
        ("cheque", "Cheque"),
        ("wire_transfer", "Wire Transfer"),
        ("other", "Other"),
    )

    PAYMENT_STATUS_CHOICES = (
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    )

    PAYMENT_VERIFICATION_STATUS_CHOICES = (
        ("pending", "Pending"),
        ("verified", "Verified"),
        ("rejected", "Rejected"),
    )

    CURRENCY_CHOICES = (
        ("INR", "INR"),
        ("USD", "USD"),
    )

    membership = models.ForeignKey(
        Membership, on_delete=models.CASCADE, related_name="payments"
    )
    payment_proof = models.FileField(
        upload_to="payment_proofs/", blank=True, null=True)
    payment_date = models.DateField(auto_now_add=True)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES)
    method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending")
    verification_status = models.CharField(
        max_length=20, choices=PAYMENT_VERIFICATION_STATUS_CHOICES, default="pending")
    verified_at = models.DateTimeField(blank=True, null=True)
    verified_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True, related_name="verified_payments")
    verification_remarks = models.TextField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.membership.company_name} - {self.amount} {self.currency}"


class Quotation(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("under_review", "Under Review"),
        ("sent", "Sent"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    )

    CURRENCY_CHOICES = (
        ("INR", "INR"),
        ("USD", "USD"),
    )

    membership = models.ForeignKey(
        Membership, on_delete=models.CASCADE, related_name="quotations"
    )
    country = models.CharField(max_length=100)
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    authority_department = models.CharField(
        max_length=255, blank=True, null=True)
    authority_website = models.URLField(blank=True, null=True)
    authority_contact_details = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default="pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Quotation #{self.id} - {self.title}"


class QuotationItem(models.Model):
    CURRENCY_CHOICES = (
        ("INR", "INR"),
        ("USD", "USD"),
    )
    quotation = models.ForeignKey(
        Quotation, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    currency = models.CharField(
        max_length=10, choices=CURRENCY_CHOICES, null=True, blank=True)
    quoted_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True)
    quoted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.product.product_name}"


class QuotationGuidelineFile(models.Model):
    quotation = models.ForeignKey(
        Quotation, on_delete=models.CASCADE, related_name="guideline_files"
    )
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file = models.FileField(
        upload_to="quotation_guidelines/", null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name or self.file.name


'''
# ------------------------------------------------------------
# 5️⃣ ORDER – Generated from accepted quotation
# ------------------------------------------------------------
class Order(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE)
    billing_info = models.TextField()
    status = models.CharField(
        max_length=50,
        default="Pending",
        choices=[
            ("Pending", "Pending"),
            ("Processing", "Processing"),
            ("Completed", "Completed"),
            ("Cancelled", "Cancelled"),
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items")
    quotation_item = models.ForeignKey(
        QuotationItem, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    service_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    unit = models.CharField(max_length=50, default="Service")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.service_name} ({self.product.product_name})"


# ------------------------------------------------------------
# 6️⃣ INVOICE – Generated per order
# ------------------------------------------------------------
class Invoice(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=50, unique=True)
    billing_date = models.DateField(auto_now_add=True)
    payment_status = models.CharField(
        max_length=50,
        default="Unpaid",
        choices=[
            ("Unpaid", "Unpaid"),
            ("Partially Paid", "Partially Paid"),
            ("Paid", "Paid"),
        ],
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.invoice_number


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="items")
    order_item = models.ForeignKey(
        OrderItem, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.description} ({self.quantity} x {self.unit_price})"


# ------------------------------------------------------------
# 7️⃣ PAYMENT – Linked to invoice
# ------------------------------------------------------------
class Payment(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_mode = models.CharField(
        max_length=50,
        default="Bank Transfer",
        choices=[
            ("Bank Transfer", "Bank Transfer"),
            ("PayPal", "PayPal"),
            ("Razorpay", "Razorpay"),
        ],
    )
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_status = models.CharField(
        max_length=50,
        default="Pending",
        choices=[
            ("Pending", "Pending"),
            ("Verified", "Verified"),
            ("Failed", "Failed"),
        ],
    )
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.transaction_id or self.id}"


# ------------------------------------------------------------
# 8️⃣ HERO IMAGES, EVENTS, NOTICES (Frontend CMS)
# ------------------------------------------------------------
class HeroImage(models.Model):
    image = models.ImageField(upload_to="hero_images/")
    caption = models.CharField(max_length=255)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.caption


class Event(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to="event_images/")
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Notice(models.Model):
    CATEGORY_CHOICES = (
        ("notice", "Notice"),
        ("event", "Event"),
        ("update", "Update"),
        ("circular", "Circular"),
    )
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to="notice_images/")
    date = models.DateField()
    venue = models.CharField(max_length=255)
    category = models.CharField(max_length=255, choices=CATEGORY_CHOICES)
    description = models.TextField()
    objectives = models.TextField()
    registration_link = models.URLField(blank=True, null=True)
    registration_fee = models.TextField(blank=True, null=True)
    bank_details = models.TextField(blank=True, null=True)
    contact_person = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
'''
