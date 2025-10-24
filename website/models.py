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


'''
# ------------------------------------------------------------
# 2️⃣ MEMBERSHIP – Company membership under AMMA
# ------------------------------------------------------------
class Membership(models.Model):
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    cin = models.CharField(max_length=50, blank=True, null=True)
    gst = models.CharField(max_length=50, blank=True, null=True)
    tan = models.CharField(max_length=50, blank=True, null=True)
    pan = models.CharField(max_length=50, blank=True, null=True)
    vat = models.CharField(max_length=50, blank=True, null=True)
    payment_receipt = models.FileField(upload_to="membership_payments/")
    membership_type = models.CharField(max_length=100, default="Data")
    payment_status = models.CharField(max_length=50, default="Pending")
    membership_status = models.CharField(max_length=50, default="Inactive")
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name


# ------------------------------------------------------------
# 3️⃣ PRODUCT – Products for registration
# ------------------------------------------------------------






# ------------------------------------------------------------
# 4️⃣ QUOTATION – Request for product registration abroad
# ------------------------------------------------------------
class Quotation(models.Model):
    membership = models.ForeignKey(Membership, on_delete=models.CASCADE)
    country = models.CharField(max_length=100)
    currency = models.CharField(max_length=10, default="USD")
    responsible_person = models.CharField(max_length=100)
    contact = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(
        upload_to="quotation_files/", blank=True, null=True)
    authority_department = models.CharField(max_length=255)
    authority_website = models.URLField(blank=True, null=True)
    authority_contact_details = models.TextField(blank=True, null=True)
    # Pending / Sent / Accepted / Rejected
    status = models.CharField(max_length=50, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Quotation #{self.id} - {self.title}"


class QuotationItem(models.Model):
    quotation = models.ForeignKey(
        Quotation, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    service_name = models.CharField(
        max_length=255)  # e.g. "Dossier Preparation"
    description = models.TextField(blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    unit = models.CharField(max_length=50, default="Service")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remarks = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.service_name} ({self.product.product_name})"


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
