from django.db.models import Count, Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import Category, Shayari
from .serializers import CategorySerializer, ShayariSerializer, ShayariAdminSerializer
from .permissions import IsAuthorOrStaffOrReadOnly


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ShayariViewSet(viewsets.ModelViewSet):
    queryset = Shayari.objects.select_related('author', 'category')
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrStaffOrReadOnly]

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return ShayariAdminSerializer
        return ShayariSerializer

    def get_queryset(self):
        qs = self.queryset
        if not self.request.user.is_authenticated or not self.request.user.is_staff:
            qs = qs.filter(approved=True)

        query = self.request.query_params.get('q')
        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(text__icontains=query) | Q(author__username__icontains=query))

        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category__slug=category)

        author = self.request.query_params.get('author')
        if author:
            qs = qs.filter(author__username__icontains=author)

        sort = self.request.query_params.get('sort', 'latest')
        if sort == 'popular':
            qs = qs.annotate(like_count=Count('likes')).order_by('-like_count', '-created_at')
        elif sort == 'oldest':
            qs = qs.order_by('created_at')
        else:
            qs = qs.order_by('-created_at')
        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, approved=self.request.user.is_staff)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        shayari = self.get_object()
        if request.user in shayari.likes.all():
            shayari.likes.remove(request.user)
            liked = False
        else:
            shayari.likes.add(request.user)
            liked = True
        return Response({'liked': liked, 'count': shayari.likes.count()})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def save(self, request, pk=None):
        shayari = self.get_object()
        if request.user in shayari.saves.all():
            shayari.saves.remove(request.user)
            saved = False
        else:
            shayari.saves.add(request.user)
            saved = True
        return Response({'saved': saved})
