from .base import BaseProvider


class MockProvider(BaseProvider):
    def translate(self, text, source_lang, target_lang):
        return text
