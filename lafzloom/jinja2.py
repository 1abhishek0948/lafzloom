import json
from jinja2 import Environment
from markupsafe import Markup
from django.templatetags.static import static
from django.urls import reverse
from django.middleware.csrf import get_token
from django.utils.html import format_html
from django.utils.formats import date_format
from lafzloom.translations import translate


def csrf_input(request):
    return format_html(
        '<input type="hidden" name="csrfmiddlewaretoken" value="{}">',
        get_token(request),
    )


def url(view_name, *args, **kwargs):
    return reverse(view_name, args=args, kwargs=kwargs)


def breadcrumb_jsonld(breadcrumbs, home_url):
    items = [{'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': home_url}]
    items.extend(
        {
            '@type': 'ListItem',
            'position': index,
            'name': crumb['name'],
            'item': crumb['url'],
        }
        for index, crumb in enumerate(breadcrumbs, start=2)
    )
    return Markup(json.dumps({
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': items,
    }, ensure_ascii=False).replace('<', '\\u003c'))


def environment(**options):
    options.setdefault('autoescape', True)
    env = Environment(**options)
    env.globals.update(
        {
            'static': static,
            'url': url,
            'csrf_input': csrf_input,
            't': translate,
        }
    )
    env.filters['date'] = lambda value, fmt='M d, Y': date_format(value, fmt, use_l10n=False)
    env.filters['tojson'] = lambda value: Markup(
        json.dumps(value, ensure_ascii=False).replace('<', '\\u003c')
    )
    env.filters['breadcrumb_jsonld'] = breadcrumb_jsonld
    return env
