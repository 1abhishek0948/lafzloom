from django.urls import path
from . import views

app_name = 'shayari'

urlpatterns = [
    path('', views.shayari_list, name='list'),
    path('category/<slug:category_slug>/', views.category_legacy_redirect, name='legacy_category_redirect'),
    path('submit/', views.submit_shayari, name='submit'),
    path('<int:pk>/edit/', views.edit_shayari, name='edit'),
    path('<int:pk>/delete/', views.delete_shayari, name='delete'),
    path('<int:pk>/', views.shayari_detail, name='detail'),
    path('<int:pk>/like/', views.like_toggle, name='like'),
    path('<int:pk>/save/', views.save_toggle, name='save'),
]
