from rest_framework import serializers


class TranslationRequestSerializer(serializers.Serializer):
    text = serializers.CharField()
    source_lang = serializers.ChoiceField(choices=['hi', 'en', 'ur'])
    target_lang = serializers.ChoiceField(choices=['hi', 'en', 'ur'])
