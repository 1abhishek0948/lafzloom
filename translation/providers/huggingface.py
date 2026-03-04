import os
import requests
from django.conf import settings

from .base import BaseProvider, TranslationError


DEFAULT_MODEL_MAP = {
    ('hi', 'en'): 'Helsinki-NLP/opus-mt-hi-en',
    ('en', 'hi'): 'Helsinki-NLP/opus-mt-en-hi',
    ('hi', 'ur'): 'Helsinki-NLP/opus-mt-hi-ur',
    ('ur', 'hi'): 'Helsinki-NLP/opus-mt-ur-hi',
    ('en', 'ur'): 'Helsinki-NLP/opus-mt-en-ur',
    ('ur', 'en'): 'Helsinki-NLP/opus-mt-ur-en',
}


class HuggingFaceProvider(BaseProvider):
    def __init__(self):
        self.api_token = os.getenv('HF_API_TOKEN')
        if not self.api_token:
            raise TranslationError('HF_API_TOKEN is not configured')
        self.timeout = settings.TRANSLATION_TIMEOUT_SECONDS

    def _model_for(self, source_lang, target_lang):
        env_key = f'HF_MODEL_{source_lang.upper()}_{target_lang.upper()}'
        return os.getenv(env_key) or DEFAULT_MODEL_MAP.get((source_lang, target_lang))

    def _call_model(self, model, text):
        url = f'https://api-inference.huggingface.co/models/{model}'
        headers = {
            'Authorization': f'Bearer {self.api_token}',
        }
        response = requests.post(url, headers=headers, json={'inputs': text}, timeout=self.timeout)
        if response.status_code >= 400:
            raise TranslationError(f'HuggingFace error: {response.status_code} {response.text}')
        data = response.json()
        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict):
                if 'translation_text' in first:
                    return first['translation_text']
                if 'generated_text' in first:
                    return first['generated_text']
        raise TranslationError('Unexpected HuggingFace response format')

    def translate(self, text, source_lang, target_lang):
        if source_lang == target_lang:
            return text
        model = self._model_for(source_lang, target_lang)
        if model:
            return self._call_model(model, text)
        if source_lang != 'en' and target_lang != 'en':
            first_pass = self.translate(text, source_lang, 'en')
            return self.translate(first_pass, 'en', target_lang)
        raise TranslationError('No model configured for this language pair')
