from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from shayari.views import home
from lafzverse import views as static_views

urlpatterns = [
    path('', home, name='home'),
    path('healthz/', static_views.healthz, name='healthz'),
    path('privacy/', static_views.privacy, name='privacy'),
    path('about/', static_views.about, name='about'),
    path('contact/', static_views.contact, name='contact'),
    path('terms/', static_views.terms, name='terms'),
    path('accounts/', include('accounts.urls')),
    path('shayari/', include('shayari.urls')),
    path('moderation/', include('moderation.urls')),
    path('api/', include('shayari.api_urls')),
    path('api/', include('translation.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
