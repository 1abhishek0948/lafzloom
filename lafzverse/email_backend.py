import os
import ssl

from django.core.mail.backends.smtp import EmailBackend as DjangoEmailBackend
from django.utils.functional import cached_property


class EmailBackend(DjangoEmailBackend):
    @cached_property
    def ssl_context(self):
        allow_insecure = os.environ.get('EMAIL_ALLOW_INSECURE_TLS', '').strip().lower() in {
            '1',
            'true',
            'yes',
            'on',
        }
        if allow_insecure:
            context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            return context
        return super().ssl_context
