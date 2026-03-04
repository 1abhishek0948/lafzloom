from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api import CategoryViewSet, ShayariViewSet

router = DefaultRouter()
router.register(r'shayaris', ShayariViewSet, basename='shayari')
router.register(r'categories', CategoryViewSet, basename='category')

urlpatterns = [
    path('', include(router.urls)),
]
