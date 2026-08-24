from urllib.parse import urlunsplit

from django.conf import settings
from django.urls import reverse

from lafzloom.jinja2 import csrf_input as csrf_input_func


def csrf_input(request):
    return {'csrf_input': csrf_input_func(request)}


def _absolute_url(request, path):
    site_url = getattr(settings, 'SITE_URL', '')
    if site_url:
        return f'{site_url}{path}'
    return request.build_absolute_uri(path).replace('http://', 'https://', 1)


def _default_seo(request):
    path = request.path
    query = request.GET
    title = settings.SITE_NAME
    description = settings.SEO_DEFAULT_DESCRIPTION
    robots = 'index, follow'
    image_path = f'{settings.STATIC_URL}{settings.SEO_DEFAULT_IMAGE.lstrip("/")}'
    schema_type = 'WebPage'
    breadcrumbs = []

    if path == '/':
        title = 'Hindi, English & Urdu Shayari and Poetry | Lafzloom'
        description = 'Explore heartfelt Hindi, English, and Urdu shayari, save favorite verses, and share poetry on Lafzloom.'
        schema_type = 'WebSite'
    elif path == '/shayari/':
        title = 'Browse Shayari and Poetry | Lafzloom'
        description = 'Browse shayari by title, author, category, language, or popularity on Lafzloom.'
        breadcrumbs = [('Shayari', reverse('shayari:list'))]
        if query and set(query) != {'page'}:
            robots = 'noindex, follow'
    elif path in {'/about/', '/contact/', '/privacy/', '/terms/'}:
        labels = {
            '/about/': ('About Lafzloom | Shayari and Poetry Platform', 'Learn about Lafzloom, a multilingual home for discovering, writing, and sharing shayari.'),
            '/contact/': ('Contact Lafzloom | Shayari Platform', 'Contact the Lafzloom team with questions, feedback, or support requests about the shayari platform.'),
            '/privacy/': ('Privacy Policy | Lafzloom', 'Read the Lafzloom privacy policy covering accounts, content, cookies, and how the service uses information.'),
            '/terms/': ('Terms and Conditions | Lafzloom', 'Read the terms and conditions for using Lafzloom and sharing poetry and shayari.'),
        }
        title, description = labels[path]
    elif path.startswith('/accounts/') or path.startswith('/moderation/') or path.startswith('/admin/'):
        robots = 'noindex, nofollow'
    elif path.startswith('/api/') or path == '/healthz/' or path.startswith('/i18n/'):
        robots = 'noindex, nofollow'
    elif path.startswith('/shayari/'):
        robots = 'noindex, nofollow'

    jsonld = {}
    if path == '/':
        jsonld = {
            '@context': 'https://schema.org',
            '@type': 'WebSite',
            'name': settings.SITE_NAME,
            'url': _absolute_url(request, reverse('home')),
            'description': description,
            'potentialAction': {
                '@type': 'SearchAction',
                'target': f'{_absolute_url(request, reverse("shayari:list"))}?q={{search_term_string}}',
                'query-input': 'required name=search_term_string',
            },
        }

    canonical_path = urlunsplit(('', '', path, '', ''))
    if path == '/shayari/' and set(query) == {'page'}:
        canonical_path = f'{canonical_path}?page={query["page"]}'

    return {
        'seo_title': title,
        'seo_description': description,
        'seo_keywords': '',
        'seo_author': settings.SITE_NAME,
        'seo_robots': robots,
        'canonical_url': _absolute_url(request, canonical_path),
        'seo_image_url': _absolute_url(request, image_path),
        'seo_og_type': 'website',
        'seo_og_locale': request.LANGUAGE_CODE.replace('-', '_'),
        'seo_schema_type': schema_type,
        'seo_breadcrumbs': [
            {
                'name': name,
                'url': _absolute_url(request, url),
                'position': position,
            }
            for position, (name, url) in enumerate(breadcrumbs, start=1)
        ],
        'seo_jsonld_extra': jsonld,
        'seo_site_name': settings.SITE_NAME,
        'seo_home_url': _absolute_url(request, reverse('home')),
        'google_site_verification': settings.GOOGLE_SITE_VERIFICATION,
        'bing_site_verification': settings.BING_SITE_VERIFICATION,
    }


def seo(request):
    metadata = _default_seo(request)
    metadata.update(getattr(request, 'seo_overrides', {}))
    return metadata
