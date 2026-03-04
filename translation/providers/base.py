class TranslationError(Exception):
    pass


class BaseProvider:
    def translate(self, text, source_lang, target_lang):
        raise NotImplementedError
