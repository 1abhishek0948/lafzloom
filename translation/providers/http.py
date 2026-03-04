import os
import requests
from django.conf import settings

from .base import BaseProvider, TranslationError


class HttpProvider(BaseProvider):
    def __init__(self):
        self.url = os.getenv('LLM_API_URL')
        if not self.url:
            raise TranslationError('LLM_API_URL is not configured')
        self.api_key = os.getenv('LLM_API_KEY')
        self.timeout = settings.TRANSLATION_TIMEOUT_SECONDS

    def translate(self, text, source_lang, target_lang):
        payload = {
            'text': text,
            'source_lang': source_lang,
            'target_lang': target_lang,
            'style': 'poetic',
        }
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        response = requests.post(self.url, json=payload, headers=headers, timeout=self.timeout)
        if response.status_code >= 400:
            raise TranslationError(f'HTTP provider error: {response.status_code} {response.text}')
        data = response.json()
        translation = data.get('translation') or data.get('text')
        if not translation:
            raise TranslationError('Provider response missing translation')
        return translation
