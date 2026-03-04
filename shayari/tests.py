from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Category, Shayari


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
