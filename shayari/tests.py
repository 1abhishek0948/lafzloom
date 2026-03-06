import unittest
from io import BytesIO

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from .importers import import_shayari_xlsx
from .models import Category, Shayari

try:
    from openpyxl import Workbook
except Exception:
    Workbook = None


class ShayariModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass1234')
        self.category = Category.objects.create(name='Love')

    def test_shayari_str(self):
        shayari = Shayari.objects.create(
            title='Test',
            text='Sample text',
            language='hi',
            category=self.category,
            author=self.user,
            approved=True,
        )
        self.assertIn('Test', str(shayari))


class ShayariApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='tester', password='pass1234')
        self.category = Category.objects.create(name='Love')
        Shayari.objects.create(
            title='Published',
            text='Hello',
            language='hi',
            category=self.category,
            author=self.user,
            approved=True,
        )

    def test_list_shayaris(self):
        response = self.client.get('/api/shayaris/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_create_requires_auth(self):
        response = self.client.post('/api/shayaris/', {
            'title': 'New',
            'text': 'Text',
            'language': 'hi',
            'category': self.category.id,
        })
        self.assertIn(response.status_code, [401, 403])


@unittest.skipIf(Workbook is None, 'openpyxl is not installed in this environment')
class ShayariXlsxImportTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(username='admin_u', email='admin@example.com', password='pass1234')
        self.author_user = User.objects.create_user(username='poet', email='poet@example.com', password='pass1234')

    def _build_xlsx(self, rows):
        wb = Workbook()
        ws = wb.active
        ws.append(['Title', 'Text', 'Language', 'Category', 'Author'])
        for row in rows:
            ws.append(row)
        payload = BytesIO()
        wb.save(payload)
        payload.seek(0)
        payload.name = 'shayari.xlsx'
        return payload

    def test_import_creates_records_from_expected_columns(self):
        file_obj = self._build_xlsx([
            ['First', 'Line one', 'Hindi', 'Sad', 'poet'],
            ['Second', 'Line two', 'English', 'Love', ''],
        ])

        result = import_shayari_xlsx(file_obj, default_author=self.admin_user, approve=True)

        self.assertEqual(result.created, 2)
        self.assertEqual(result.skipped, 0)
        self.assertEqual(Shayari.objects.count(), 2)
        self.assertTrue(Shayari.objects.filter(title='First', language='hi', approved=True).exists())
        self.assertTrue(Shayari.objects.filter(title='Second', language='en', author=self.admin_user).exists())
        self.assertTrue(Category.objects.filter(name='Sad').exists())
        self.assertTrue(Category.objects.filter(name='Love').exists())

    def test_import_skips_invalid_language(self):
        file_obj = self._build_xlsx([
            ['Bad Row', 'Nope', 'Spanish', 'Sad', 'poet'],
        ])

        result = import_shayari_xlsx(file_obj, default_author=self.admin_user, approve=False)

        self.assertEqual(result.created, 0)
        self.assertEqual(result.skipped, 1)
        self.assertIn('invalid language', result.warnings[0].lower())

    def test_import_applies_defaults_for_blank_title_category_language(self):
        file_obj = self._build_xlsx([
            ['', 'Line with defaults', '', '', ''],
        ])

        result = import_shayari_xlsx(file_obj, default_author=self.admin_user, approve=False)

        self.assertEqual(result.created, 1)
        self.assertEqual(result.skipped, 0)
        shayari = Shayari.objects.get(text='Line with defaults')
        self.assertEqual(shayari.title, 'Untitled')
        self.assertEqual(shayari.language, 'hi')
        self.assertEqual(shayari.category.name, 'General')
