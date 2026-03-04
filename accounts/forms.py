from django import forms
from django.contrib.auth import password_validation, get_user_model
from django.contrib.auth.forms import UserCreationForm
from lafzverse.translations import translate as t


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


class VerifyEmailForm(forms.Form):
    otp = forms.CharField(
        max_length=6,
        min_length=6,
        label='Verification Code',
        widget=forms.TextInput(attrs={'autocomplete': 'one-time-code'}),
    )


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(required=True)


class ResetPasswordForm(forms.Form):
    otp = forms.CharField(
        max_length=6,
        min_length=6,
        label='Verification Code',
        widget=forms.TextInput(attrs={'autocomplete': 'one-time-code'}),
    )
    password1 = forms.CharField(
        label='New password',
        widget=forms.PasswordInput,
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get('password1')
        password2 = cleaned.get('password2')
        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Passwords do not match.')
        if password1:
            password_validation.validate_password(password1)
        return cleaned
