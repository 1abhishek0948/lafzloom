from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm, UserCreationForm
from lafzloom.translations import translate as t


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            return email
        UserModel = get_user_model()
        if UserModel.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(t('An account with this email already exists.'))
        return email


class ForgotPasswordForm(PasswordResetForm):
    email = forms.EmailField(required=True)

    def clean_email(self):
        return self.cleaned_data.get('email', '').strip().lower()
