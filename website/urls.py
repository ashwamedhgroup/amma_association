from django.urls import path
from . import views

urlpatterns = [
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/registration/', views.RegistrationView.as_view(),
         name='registration-create'),
    path('auth/profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('auth/change-password/',
         views.ChangePasswordView.as_view(), name='change-password'),
    path('auth/forgot-password/',
         views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('auth/reset-password/',
         views.ResetPasswordView.as_view(), name='reset-password'),

    # Product endpoints
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(),
         name='product-detail'),
    path('products/<int:product_id>/documents/',
         views.ProductDocumentListView.as_view(), name='product-documents'),
    path('products/<int:product_id>/registrations/',
         views.ProductRegistrationListView.as_view(), name='product-registrations'),

    # Membership endpoints
    path('memberships/', views.MembershipListView.as_view(), name='membership-list'),
    path('memberships/<int:pk>/', views.MembershipDetailView.as_view(),
         name='membership-detail'),
    path('memberships/<int:membership_id>/documents/',
         views.MembershipDocumentListView.as_view(), name='membership-documents'),
    path('memberships/<int:membership_id>/payments/',
         views.MembershipPaymentListView.as_view(), name='membership-payments'),

    # Dedicated Membership Document API endpoints
    path('membership-documents/', views.MembershipDocumentAPIView.as_view(),
         name='membership-document-api'),
    path('membership-documents/<int:document_id>/', views.MembershipDocumentAPIView.as_view(),
         name='membership-document-detail'),
    path('membership-documents/by-membership/<int:membership_id>/',
         views.MembershipDocumentByMembershipView.as_view(), name='membership-documents-by-membership'),

    # Dedicated Membership Payment API endpoints
    path('membership-payments/', views.MembershipPaymentAPIView.as_view(),
         name='membership-payment-api'),
    path('membership-payments/<int:payment_id>/', views.MembershipPaymentAPIView.as_view(),
         name='membership-payment-detail'),
    path('membership-payments/by-membership/<int:membership_id>/',
         views.MembershipPaymentByMembershipView.as_view(), name='membership-payments-by-membership'),

    # Dedicated Quotation API endpoints
    path('quotations/', views.QuotationAPIView.as_view(),
         name='quotation-api'),
    path('quotations/<int:quotation_id>/', views.QuotationAPIView.as_view(),
         name='quotation-detail'),
    path('quotations/by-membership/<int:membership_id>/',
         views.QuotationByMembershipView.as_view(), name='quotations-by-membership'),
]
