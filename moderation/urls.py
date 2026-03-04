from django.urls import path
from . import views

app_name = 'moderation'

urlpatterns = [
    path('', views.pending, name='pending'),
    path('<int:pk>/approve/', views.approve, name='approve'),
    path('<int:pk>/unpublish/', views.unpublish, name='unpublish'),
    path('<int:pk>/reject/', views.reject, name='reject'),
    path('<int:pk>/edit/', views.edit, name='edit'),
]
