from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from shayari.models import Category, Shayari


@override_settings(
    SITE_URL='https://lafzloom.example',
    DEBUG=False,
    DEBUG_PROPAGATE_EXCEPTIONS=False,
    SECRET_KEY='test-seo-secret-key-that-is-long-enough-for-django',
    ALLOWED_HOSTS=['testserver'],
    STORAGES={
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    },
    SECURE_SSL_REDIRECT=False,
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
)
class SeoTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Love')
        self.user = User.objects.create_user(username='poet', password='pass1234')
        self.shayari = Shayari.objects.create(
            title='A published verse',
            text='A heartfelt line about love and memory.',
            language='en',
            category=self.category,
            author=self.user,
            approved=True,
        )

    def assert_seo_head(self, response, *, robots='index, follow'):
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn('<title>', body)
        self.assertIn('<meta name="description"', body)
        self.assertIn(f'<meta name="robots" content="{robots}">', body)
        self.assertIn('<link rel="canonical" href="https://lafzloom.example/', body)
        self.assertIn('<meta property="og:title"', body)
        self.assertIn('<meta name="twitter:card"', body)
        self.assertIn('application/ld+json', body)

    def test_public_pages_have_seo_metadata(self):
        for path in ('/', '/shayari/', '/about/', '/contact/'):
            with self.subTest(path=path):
                self.assert_seo_head(self.client.get(path))

    def test_category_and_detail_pages_have_indexable_metadata(self):
        category_response = self.client.get('/category/love/')
        detail_response = self.client.get(f'/shayari/{self.shayari.pk}/')
        self.assert_seo_head(category_response)
        self.assert_seo_head(detail_response)
        self.assertIn('Love Shayari', category_response.content.decode())
        self.assertIn('A published verse', detail_response.content.decode())
        self.assertIn('CreativeWork', detail_response.content.decode())

    def test_search_and_private_pages_are_not_indexable(self):
        search_response = self.client.get('/shayari/?q=love')
        self.assert_seo_head(search_response, robots='noindex, follow')
        login = self.client.get('/accounts/login/')
        self.assertEqual(login.status_code, 200)
        self.assertIn('noindex, nofollow', login.content.decode())

    def test_robots_and_sitemap_exclude_private_paths(self):
        robots = self.client.get('/robots.txt')
        self.assertEqual(robots.status_code, 200)
        self.assertIn('Sitemap: https://lafzloom.example/sitemap.xml', robots.content.decode())
        self.assertIn('Disallow: /admin/', robots.content.decode())
        self.assertNotIn('Disallow: /static/', robots.content.decode())

        sitemap = self.client.get('/sitemap.xml')
        self.assertEqual(sitemap.status_code, 200)
        sitemap_body = sitemap.content.decode()
        self.assertIn('/category/love/', sitemap_body)
        self.assertIn(f'/shayari/{self.shayari.pk}/', sitemap_body)
        self.assertNotIn('/accounts/', sitemap_body)

    def test_missing_pages_return_seo_safe_404(self):
        response = self.client.get('/does-not-exist/')
        self.assertEqual(response.status_code, 404)
        self.assertIn('noindex, nofollow', response.content.decode())
