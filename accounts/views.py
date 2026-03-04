import json
import logging
import re
import secrets
from datetime import timedelta

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from .forms import RegisterForm, VerifyEmailForm, ForgotPasswordForm, ResetPasswordForm
from .models import EmailOTP
from lafzverse.firebase_admin import get_firebase_app
from lafzverse.translations import translate as t
from shayari.models import Shayari

logger = logging.getLogger(__name__)


def _generate_otp():
    return f"{secrets.randbelow(1_000_000):06d}"


def _send_otp_email(subject, message, from_email, to_email):
    provider = getattr(settings, 'OTP_EMAIL_PROVIDER', 'smtp')
    timeout = getattr(settings, 'EMAIL_TIMEOUT', 15)

    if provider == 'resend':
        api_key = getattr(settings, 'RESEND_API_KEY', '')
        if not api_key:
            raise RuntimeError('RESEND_API_KEY is required when OTP_EMAIL_PROVIDER=resend')
        response = requests.post(
            'https://api.resend.com/emails',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'from': getattr(settings, 'RESEND_FROM_EMAIL', from_email) or from_email,
                'to': [to_email],
                'subject': subject,
                'text': message,
            },
            timeout=timeout,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Resend email failed: {response.status_code} {response.text}")
        return

    send_mail(subject, message, from_email, [to_email], fail_silently=False)


def _send_email_otp(email, purpose, user=None):
    expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
    expires_at = timezone.now() + timedelta(minutes=expiry_minutes)

    EmailOTP.objects.filter(email=email, purpose=purpose, is_used=False).update(is_used=True)
    otp = EmailOTP.objects.create(
        user=user,
        email=email,
        code=_generate_otp(),
        purpose=purpose,
        expires_at=expires_at,
    )

    if purpose == EmailOTP.PURPOSE_SIGNUP:
        subject = t('Verify your Lafzverse email')
        message = t('Your verification code is {code}. It expires in {minutes} minutes.').format(
            code=otp.code,
            minutes=expiry_minutes,
        )
    else:
        subject = t('Reset your Lafzverse password')
        message = t('Your password reset code is {code}. It expires in {minutes} minutes.').format(
            code=otp.code,
            minutes=expiry_minutes,
        )

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', '') or getattr(settings, 'EMAIL_HOST_USER', '')
    if not from_email:
        from_email = 'no-reply@lafzverse.com'

    try:
        _send_otp_email(subject, message, from_email, email)
    except Exception:
        otp.is_used = True
        otp.save(update_fields=['is_used'])
        raise
    return otp


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            if getattr(settings, 'FIREBASE_AUTH_ENABLED', False):
                messages.info(request, t('Use Firebase sign-up to create your account.'))
                return redirect('accounts:register')
            email = form.cleaned_data['email'].strip().lower()
            pending_signup = {
                'username': form.cleaned_data['username'],
                'email': email,
                'password_hash': make_password(form.cleaned_data['password1']),
            }
            try:
                _send_email_otp(email, EmailOTP.PURPOSE_SIGNUP)
            except Exception:
                logger.exception("Failed to send signup OTP email to %s", email)
                form.add_error(None, t('Unable to send verification email. Please try again later.'))
                return render(request, 'accounts/register.jinja', {'form': form})
            request.session['pending_verification_email'] = email
            request.session['pending_signup'] = pending_signup
            messages.info(request, t('We sent a verification code to your email.'))
            return redirect('accounts:verify_email')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.jinja', {'form': form})


@login_required
def profile(request):
    my_shayaris = Shayari.objects.filter(author=request.user).order_by('-created_at')
    saved_shayaris = request.user.saved_shayaris.all().order_by('-created_at')
    liked_shayaris = request.user.liked_shayaris.all().order_by('-created_at')
    return render(
        request,
        'accounts/profile.jinja',
        {
            'my_shayaris': my_shayaris,
            'saved_shayaris': saved_shayaris,
            'liked_shayaris': liked_shayaris,
        },
    )


@require_http_methods(["GET", "POST"])
def logout_view(request):
    logout(request)
    next_url = request.GET.get('next') or request.POST.get('next') or ''
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect('home')


@require_http_methods(["POST"])
def firebase_login(request):
    if not getattr(settings, 'FIREBASE_AUTH_ENABLED', False):
        return JsonResponse({'error': 'FIREBASE_DISABLED'}, status=400)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'INVALID_JSON'}, status=400)

    id_token = payload.get('id_token')
    if not id_token:
        return JsonResponse({'error': 'MISSING_ID_TOKEN'}, status=400)

    app = get_firebase_app()
    if not app:
        return JsonResponse({'error': 'FIREBASE_NOT_CONFIGURED'}, status=500)

    try:
        from firebase_admin import auth as firebase_auth
        decoded = firebase_auth.verify_id_token(id_token, app=app)
    except Exception:
        return JsonResponse({'error': 'INVALID_ID_TOKEN'}, status=401)

    email = decoded.get('email')
    if not email:
        return JsonResponse({'error': 'EMAIL_REQUIRED'}, status=400)

    if getattr(settings, 'FIREBASE_REQUIRE_EMAIL_VERIFIED', False) and not decoded.get('email_verified'):
        return JsonResponse({'error': 'EMAIL_NOT_VERIFIED'}, status=403)

    UserModel = get_user_model()
    user = UserModel.objects.filter(email__iexact=email).first()
    if not user:
        username = _generate_username(email)
        user = UserModel.objects.create(username=username, email=email)
        user.set_unusable_password()
        user.save()

    login(request, user, backend='accounts.backends.EmailOrUsernameModelBackend')
    return JsonResponse({'ok': True})


def verify_email(request):
    pending_email = request.session.get('pending_verification_email')
    pending_signup = request.session.get('pending_signup')
    if not pending_email:
        messages.info(request, t('Please register to receive a verification code.'))
        return redirect('accounts:register')
    if not pending_signup:
        messages.info(request, t('Please register to receive a verification code.'))
        return redirect('accounts:register')

    if request.method == 'POST':
        form = VerifyEmailForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['otp']
            otp = (
                EmailOTP.objects.filter(
                    email__iexact=pending_email,
                    purpose=EmailOTP.PURPOSE_SIGNUP,
                    code=code,
                    is_used=False,
                    expires_at__gte=timezone.now(),
                )
                .order_by('-created_at')
                .first()
            )
            if not otp:
                form.add_error('otp', t('Invalid or expired code.'))
            else:
                UserModel = get_user_model()
                if UserModel.objects.filter(email__iexact=pending_email).exists():
                    form.add_error(None, t('An account with this email already exists.'))
                elif UserModel.objects.filter(username__iexact=pending_signup['username']).exists():
                    form.add_error(None, t('Username is already taken.'))
                else:
                    user = UserModel(
                        username=pending_signup['username'],
                        email=pending_email,
                        is_active=True,
                    )
                    password_hash = pending_signup.get('password_hash')
                    if password_hash:
                        # Backward compatibility for sessions created before this update.
                        user.password = password_hash
                    else:
                        user.set_password(pending_signup.get('password', ''))
                    user.save()
                    otp.is_used = True
                    otp.save(update_fields=['is_used'])
                    request.session.pop('pending_verification_email', None)
                    request.session.pop('pending_signup', None)
                    login(request, user, backend='accounts.backends.EmailOrUsernameModelBackend')
                    messages.success(request, t('Your email is verified. Welcome!'))
                    return redirect('home')
    else:
        form = VerifyEmailForm()
    return render(request, 'accounts/verify_email.jinja', {'form': form})


def forgot_password(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].strip().lower()
            user = get_user_model().objects.filter(email__iexact=email).first()
            if user:
                try:
                    _send_email_otp(email, EmailOTP.PURPOSE_RESET, user=user)
                except Exception:
                    logger.exception("Failed to send password-reset OTP email to %s", email)
                    form.add_error(None, t('Unable to send reset email. Please try again later.'))
                    return render(request, 'accounts/forgot_password.jinja', {'form': form})
            request.session['pending_reset_email'] = email
            messages.info(request, t('If an account exists, a reset code was sent.'))
            return redirect('accounts:reset_password')
    else:
        form = ForgotPasswordForm()
    return render(request, 'accounts/forgot_password.jinja', {'form': form})


def reset_password(request):
    pending_email = request.session.get('pending_reset_email')
    if not pending_email:
        messages.info(request, t('Enter your email to receive a reset code.'))
        return redirect('accounts:forgot_password')

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['otp']
            otp = (
                EmailOTP.objects.filter(
                    email__iexact=pending_email,
                    purpose=EmailOTP.PURPOSE_RESET,
                    code=code,
                    is_used=False,
                    expires_at__gte=timezone.now(),
                )
                .order_by('-created_at')
                .first()
            )
            if not otp:
                form.add_error('otp', t('Invalid or expired code.'))
            else:
                user = get_user_model().objects.filter(email__iexact=pending_email).first()
                if not user:
                    form.add_error(None, t('Invalid or expired code.'))
                else:
                    user.set_password(form.cleaned_data['password1'])
                    user.save()
                    otp.is_used = True
                    otp.save(update_fields=['is_used'])
                    request.session.pop('pending_reset_email', None)
                    messages.success(request, t('Password reset successful. Please log in.'))
                    return redirect('accounts:login')
    else:
        form = ResetPasswordForm()
    return render(request, 'accounts/reset_password.jinja', {'form': form})


def _generate_username(email):
    base = email.split('@')[0]
    base = re.sub(r'[^a-zA-Z0-9_]+', '', base) or 'user'
    UserModel = get_user_model()
    candidate = base
    counter = 1
    while UserModel.objects.filter(username=candidate).exists():
        candidate = f"{base}{counter}"
        counter += 1
    return candidate
