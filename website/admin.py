from django.contrib import admin
from .models import Registration, Product, ProductRegistration, ProductDocument

# Register your models here.
admin.site.register(Registration)
admin.site.register(Product)
admin.site.register(ProductRegistration)
admin.site.register(ProductDocument)
