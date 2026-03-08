from django.urls import path

from . import views

urlpatterns = [
    # Auth
    path('auth/register', views.RegisterView.as_view(), name='register'),
    path('auth/login', views.LoginView.as_view(), name='login'),
    path('auth/refresh', views.RefreshTokenView.as_view(), name='refresh'),
    path('auth/logout', views.LogoutView.as_view(), name='logout'),
    path('auth/forgot-password', views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('auth/reset-password', views.ResetPasswordView.as_view(), name='reset-password'),
    # Users
    path('users/me', views.ProfileView.as_view(), name='profile'),
    path('users/me/avatar', views.AvatarUploadView.as_view(), name='avatar-upload'),
    path('users/me/change-password', views.ChangePasswordView.as_view(), name='change-password'),
]
