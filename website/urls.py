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
]
