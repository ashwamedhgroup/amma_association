from django.contrib import admin
from .models import Registration, Product, ProductRegistration, ProductDocument, Membership, MembershipDocument, MembershipPayment, Quotation, QuotationItem, QuotationGuidelineFile

# Register your models here.
admin.site.register(Registration)
admin.site.register(Product)
admin.site.register(ProductRegistration)
admin.site.register(ProductDocument)
admin.site.register(Membership)
admin.site.register(MembershipDocument)
admin.site.register(MembershipPayment)
admin.site.register(Quotation)
admin.site.register(QuotationItem)
admin.site.register(QuotationGuidelineFile)
