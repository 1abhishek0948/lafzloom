from django.conf import settings
from django.db import models


class EmailOTP(models.Model):
    PURPOSE_SIGNUP = 'signup'
    PURPOSE_RESET = 'reset'
    PURPOSE_CHOICES = [
        (PURPOSE_SIGNUP, 'Signup'),
        (PURPOSE_RESET, 'Password Reset'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='email_otps',
        null=True,
        blank=True,
    )
    email = models.EmailField()
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=10, choices=PURPOSE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['email', 'purpose']),
            models.Index(fields=['user', 'purpose']),
        ]

    def __str__(self):
        return f"{self.email} ({self.purpose})"
