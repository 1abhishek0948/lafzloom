from django.conf import settings

from .providers.base import TranslationError
from .providers.mock import MockProvider
from .providers.huggingface import HuggingFaceProvider
from .providers.http import HttpProvider


def get_provider():
    provider = settings.TRANSLATION_PROVIDER
    if provider == 'hf':
        try:
            return HuggingFaceProvider()
        except TranslationError:
            return MockProvider()
    if provider == 'http':
        try:
            return HttpProvider()
        except TranslationError:
            return MockProvider()
    return MockProvider()
