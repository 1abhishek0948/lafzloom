from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from shayari.models import Category, Shayari


def absolute_url(request, path):
    if settings.SITE_URL:
        return f'{settings.SITE_URL.rstrip("/")}{path}'
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
    if request.GET.get('page') and page.number > 1:
        canonical = f'{canonical}?page={page.number}'
    category_url = absolute_url(request, reverse('category', kwargs={'category_slug': category.slug}))
    request.seo_overrides = {
        'seo_title': f'{category.name} Shayari and Poetry | Lafzloom',
        'seo_description': category.description or f'Read the latest {category.name} shayari and poetry shared on Lafzloom.',
        'seo_robots': 'index, follow' if page.paginator.count else 'noindex, follow',
        'canonical_url': canonical,
        'seo_breadcrumbs': [
            {'name': 'Shayari', 'url': absolute_url(request, reverse('shayari:list')), 'position': 1},
            {'name': category.name, 'url': category_url, 'position': 2},
        ],
    }
    return render(request, 'shayari/category.jinja', {
        'category': category,
        'shayaris': page.object_list,
        'page_obj': page,
    })


def healthz(request):
    return JsonResponse({'status': 'ok'})


def google_site_verification(request):
    content = 'google-site-verification: google2edb0a36fd4a1449.html'
    return HttpResponse(content, content_type='text/html')


def robots_txt(request):
    sitemap_url = absolute_url(request, reverse('sitemap'))
    private_rules = [
        'Disallow: /admin/',
        'Disallow: /accounts/',
        'Disallow: /moderation/',
        'Disallow: /api/',
        'Disallow: /healthz/',
        'Disallow: /i18n/',
        'Disallow: /shayari/submit/',
        'Disallow: /shayari/*/edit/',
        'Disallow: /shayari/*/delete/',
    ]
    ai_crawlers = [
        'GPTBot',
        'OAI-SearchBot',
        'ChatGPT-User',
        'ClaudeBot',
        'Claude-Web',
        'PerplexityBot',
        'Perplexity-User',
        'Google-Extended',
        'Applebot',
        'Applebot-Extended',
        'Amazonbot',
        'meta-externalagent',
        'CCBot',
    ]
    content = [
        '# robots.txt for Lafzloom',
        '',
        '# All crawlers',
        'User-agent: *',
        'Allow: /',
        *private_rules,
        '',
        '# Search engine crawlers (explicitly allowed)',
        'User-agent: Googlebot',
        'Allow: /',
        'User-agent: Bingbot',
        'Allow: /',
        '',
        '# AI/LLM crawlers (explicitly allowed so shayari can be cited in AI answers)',
    ]
    for bot in ai_crawlers:
        content.extend([f'User-agent: {bot}', 'Allow: /'])
    content.extend([
        '',
        f'Sitemap: {sitemap_url}',
        '',
    ])
    return HttpResponse('\n'.join(content), content_type='text/plain')


def llms_txt(request):
    home_url = absolute_url(request, '/')
    browse_url = absolute_url(request, reverse('shayari:list'))
    categories = (
        Category.objects.filter(shayaris__approved=True)
        .annotate(approved_count=Count('shayaris', filter=Q(shayaris__approved=True)))
        .order_by('-approved_count')
    )
    lines = [
        f'# {settings.SITE_NAME}',
        '',
        f'> {settings.SEO_DEFAULT_DESCRIPTION}',
        '',
        f'{settings.SITE_NAME} is a multilingual shayari and poetry platform available in English, Hindi, and Urdu. '
        'Visitors can browse human-moderated, community-submitted shayari by category, author, or popularity. '
        'Registered users can submit shayari, like, save, and curate collections.',
        '',
        '## Pages',
        '',
        f'- [Home]({home_url}): Latest approved shayari and featured categories.',
        f'- [Browse Shayari]({browse_url}): Full shayari library with search, category, author, and popularity filters.',
        f'- [About]({absolute_url(request, reverse("about"))}): What Lafzloom is and how it works.',
        f'- [Contact]({absolute_url(request, reverse("contact"))}): Support and inquiries.',
        f'- [Privacy Policy]({absolute_url(request, reverse("privacy"))}): Data handling and privacy practices.',
        f'- [Terms of Service]({absolute_url(request, reverse("terms"))}): Rules for using Lafzloom.',
        '',
        '## Categories',
        '',
    ]
    for category in categories:
        description = category.description or f'{category.name} shayari and poetry'
        category_url = absolute_url(request, reverse('category', kwargs={'category_slug': category.slug}))
        lines.append(
            f'- [{category.name}]({category_url}): {description} '
            f'({category.approved_count} approved shayari).'
        )
    lines.extend([
        '',
        '## Notes',
        '',
        '- All shayari are reviewed by human moderators before appearing publicly.',
        '- Content is written in Hindi, English, and Urdu; the interface supports all three languages.',
        '- Shayari detail pages include the full text, author, category, and like/save counts.',
    ])
    return HttpResponse('\n'.join(lines) + '\n', content_type='text/plain; charset=utf-8')


def error_404(request, exception):
    request.seo_overrides = {
        'seo_title': 'Page Not Found | Lafzloom',
        'seo_description': 'The requested page could not be found on Lafzloom.',
        'seo_robots': 'noindex, nofollow',
    }
    return render(request, '404.jinja', status=404)


def error_500(request):
    request.seo_overrides = {
        'seo_title': 'Something Went Wrong | Lafzloom',
        'seo_description': 'Lafzloom is temporarily unable to complete this request.',
        'seo_robots': 'noindex, nofollow',
    }
    return render(request, '500.jinja', status=500)
