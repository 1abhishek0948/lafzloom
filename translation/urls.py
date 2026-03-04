from django.urls import path
from .views import TranslateView

urlpatterns = [
    path('translate/', TranslateView.as_view(), name='translate'),
]
