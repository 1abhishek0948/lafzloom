from django.conf import settings
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from shayari.models import Category, Shayari


def absolute_url(request, path):
    if settings.SITE_URL:
        return f'{settings.SITE_URL}{path}'
    return request.build_absolute_uri(path).replace('http://', 'https://', 1)


def about(request):
    return render(request, 'pages/about.jinja')


def contact(request):
    return render(request, 'pages/contact.jinja')


def privacy(request):
    return render(request, 'pages/privacy.jinja')


def terms(request):
    return render(request, 'pages/terms.jinja')


def category_detail(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    page = Paginator(
        Shayari.objects.filter(approved=True, category=category)
        .select_related('author', 'category')
        .order_by('-created_at'),
        12,
    ).get_page(request.GET.get('page'))
    canonical = absolute_url(request, reverse('category', kwargs={'category_slug': category.slug}))
    if request.GET.get('page'):
        canonical = f'{canonical}?page={page.number}'
    request.seo_overrides = {
        'seo_title': f'{category.name} Shayari and Poetry | Lafzloom',
        'seo_description': category.description or f'Read the latest {category.name} shayari and poetry shared on Lafzloom.',
        'canonical_url': canonical,
        'seo_breadcrumbs': [
            {'name': 'Shayari', 'url': absolute_url(request, reverse('shayari:list')), 'position': 1},
            {'name': category.name, 'url': canonical, 'position': 2},
        ],
    }
    return render(request, 'shayari/category.jinja', {
        'category': category,
        'shayaris': page.object_list,
        'page_obj': page,
    })


def healthz(request):
    return JsonResponse({'status': 'ok'})


def robots_txt(request):
    site_url = settings.SITE_URL or request.build_absolute_uri('/').rstrip('/')
    hostname = site_url.split('://', 1)[-1].rstrip('/')
    content = '\n'.join([
        'User-agent: *',
        'Allow: /',
        'Disallow: /admin/',
        'Disallow: /accounts/',
        'Disallow: /moderation/',
        'Disallow: /api/',
        'Disallow: /healthz/',
        'Disallow: /i18n/',
        'Disallow: /shayari/submit/',
        'Disallow: /shayari/*/edit/',
        'Disallow: /shayari/*/delete/',
        f'Sitemap: https://{hostname}/sitemap.xml',
        '',
    ])
    return HttpResponse(content, content_type='text/plain')


def error_404(request, exception):
    request.seo_overrides = {
        'seo_title': 'Page Not Found | Lafzloom',
        'seo_description': 'The requested page could not be found on Lafzloom.',
        'seo_robots': 'noindex, nofollow',
    }
    return render(request, '404.jinja', status=404)
