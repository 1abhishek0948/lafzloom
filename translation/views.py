from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import TranslationRequestSerializer
from .services import get_provider
from .utils import ensure_script
from .providers.base import TranslationError


class TranslateView(APIView):
    def post(self, request):
        serializer = TranslationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        provider = get_provider()
        try:
            translated = provider.translate(data['text'], data['source_lang'], data['target_lang'])
            translated = ensure_script(translated, data['target_lang'])
        except TranslationError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({'translation': translated})
