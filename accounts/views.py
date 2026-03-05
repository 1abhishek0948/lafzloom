import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetConfirmView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from .forms import ForgotPasswordForm, RegisterForm
from lafzverse.translations import translate as t
from shayari.models import Shayari

logger = logging.getLogger(__name__)


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            UserModel = get_user_model()
            email = form.cleaned_data['email'].strip().lower()
            user = UserModel.objects.create_user(
                username=form.cleaned_data['username'],
                email=email,
                password=form.cleaned_data['password1'],
            )
            login(request, user, backend='accounts.backends.EmailOrUsernameModelBackend')
            messages.success(request, t('Welcome! Your account is ready.'))
            return redirect('home')
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


def forgot_password(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            try:
                form.save(
                    request=request,
                    use_https=request.is_secure(),
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', ''),
                    subject_template_name='accounts/password_reset_subject.txt',
                    email_template_name='accounts/password_reset_email.txt',
                )
            except Exception:
                logger.exception("Failed to send password reset email")
                form.add_error(None, t('Unable to send reset email. Please try again later.'))
                return render(request, 'accounts/forgot_password.jinja', {'form': form})
            messages.info(request, t('Check your email for a reset link.'))
            return redirect('accounts:login')
    else:
        form = ForgotPasswordForm()
    return render(request, 'accounts/forgot_password.jinja', {'form': form})


class ResetPasswordConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/reset_password.jinja'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        messages.success(self.request, t('Password reset complete. You can log in now.'))
        return super().form_valid(form)
