from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from shayari.models import Category, Shayari


class StaticSitemap(Sitemap):
    changefreq = 'weekly'

    def items(self):
        return ['home', 'shayari:list', 'about', 'contact']

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return 1.0 if item == 'home' else 0.6


class ShayariSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.7

    def items(self):
        return Shayari.objects.filter(approved=True).select_related('author', 'category')

    def location(self, item):
        return reverse('shayari:detail', kwargs={'pk': item.pk})

    def lastmod(self, item):
        return item.updated_at


class CategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.6

    def items(self):
        return Category.objects.filter(shayaris__approved=True).distinct()

    def location(self, item):
        return reverse('category', kwargs={'category_slug': item.slug})


def sitemap_items():
    return {
        'static': StaticSitemap(),
        'categories': CategorySitemap(),
        'shayari': ShayariSitemap(),
    }
