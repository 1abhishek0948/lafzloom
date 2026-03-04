from django.urls import path
from . import views

app_name = 'shayari'

urlpatterns = [
    path('', views.shayari_list, name='list'),
    path('category/<slug:category_slug>/', views.shayari_list, name='list_by_category'),
    path('submit/', views.submit_shayari, name='submit'),
    path('<int:pk>/edit/', views.edit_shayari, name='edit'),
    path('<int:pk>/delete/', views.delete_shayari, name='delete'),
    path('<int:pk>/', views.shayari_detail, name='detail'),
    path('<int:pk>/like/', views.like_toggle, name='like'),
    path('<int:pk>/save/', views.save_toggle, name='save'),
]
