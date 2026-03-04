from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from shayari.models import Category, Shayari


class Command(BaseCommand):
    help = 'Seed the database with sample categories and shayaris.'

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(username='demo', defaults={'email': 'demo@lafzverse.com'})
        if created:
            user.set_password('demo1234')
            user.save()
            self.stdout.write(self.style.SUCCESS('Created demo user (demo/demo1234).'))

        categories = [
            ('Love', 'Dil se nikli nazmein.'),
            ('Sad', 'Khamosh dard ki aawaaz.'),
            ('Motivational', 'Hausla aur umeed se bhari lines.'),
            ('Friendship', 'Dosti ke lamhe.'),
            ('Life', 'Zindagi ke rang.'),
        ]

        category_map = {}
        for name, desc in categories:
            category, _ = Category.objects.get_or_create(name=name, defaults={'description': desc})
            category_map[name] = category

        shayaris = [
            {
                'title': 'Raat Ka Sukoon',
                'text': 'Chandni raat mein teri yaad aayi,\nKhamoshi ne bhi apni kahani sunayi.',
                'language': 'hi',
                'category': 'Love',
            },
            {
                'title': 'Hope Sparks',
                'text': 'Even in the darkest night,\nA spark of hope keeps the heart alight.',
                'language': 'en',
                'category': 'Motivational',
            },
            {
                'title': 'Dosti Ka Rang',
                'text': 'Doston ki baaton mein rahat si hai,\nHar musibat mein bas saath ki hai.',
                'language': 'hi',
                'category': 'Friendship',
            },
            {
                'title': 'Khamosh Dard',
                'text': 'Dard chupane ke liye muskurate rahe,\nAndar hi andar toot-te rahe.',
                'language': 'hi',
                'category': 'Sad',
            },
            {
                'title': 'Zindagi',
                'text': 'Zindagi ek safar hai,\nHar mod par ek nayi nazar hai.',
                'language': 'hi',
                'category': 'Life',
            },
        ]

        for item in shayaris:
            Shayari.objects.get_or_create(
                title=item['title'],
                author=user,
                defaults={
                    'text': item['text'],
                    'language': item['language'],
                    'category': category_map[item['category']],
                    'approved': True,
                },
            )

        self.stdout.write(self.style.SUCCESS('Seed data added.'))
