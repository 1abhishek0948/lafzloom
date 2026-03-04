from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    register,
    profile,
    logout_view,
    firebase_login,
    verify_email,
    forgot_password,
    reset_password,
)

app_name = 'accounts'

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.jinja'), name='login'),
    path('logout/', logout_view, name='logout'),
    path('firebase-login/', firebase_login, name='firebase_login'),
    path('profile/', profile, name='profile'),
    path('verify-email/', verify_email, name='verify_email'),
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('reset-password/', reset_password, name='reset_password'),
]
