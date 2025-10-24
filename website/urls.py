from django.urls import path
from . import views

urlpatterns = [
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/registration/', views.RegistrationView.as_view(),
         name='registration-create'),
    path('auth/profile/', views.UserProfileView.as_view(), name='user-profile'),
]
