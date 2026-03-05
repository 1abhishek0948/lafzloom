import json
from jinja2 import Environment
from markupsafe import Markup
from django.templatetags.static import static
from django.urls import reverse
from django.middleware.csrf import get_token
from django.utils.html import format_html
from django.utils.formats import date_format
from lafzverse.translations import translate


def csrf_input(request):
    return format_html(
        '<input type="hidden" name="csrfmiddlewaretoken" value="{}">',
        get_token(request),
    )


def url(view_name, *args, **kwargs):
    return reverse(view_name, args=args, kwargs=kwargs)


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
    env.filters['tojson'] = lambda value: Markup(json.dumps(value))
    return env
