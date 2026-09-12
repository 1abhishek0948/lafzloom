from django.contrib.sitemaps import Sitemap
from django.db.models import OuterRef, Subquery
from django.urls import reverse

from shayari.models import Category, Shayari


class StaticSitemap(Sitemap):
    changefreq = 'weekly'

    def items(self):
        return ['home', 'shayari:list', 'about', 'contact', 'privacy', 'terms']

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        if item == 'home':
            return 1.0
        if item == 'shayari:list':
            return 0.9
        return 0.5


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
    changefreq = 'daily'
    priority = 0.8

    def items(self):
        latest = (
            Shayari.objects.filter(category=OuterRef('pk'), approved=True)
            .order_by('-updated_at')
            .values('updated_at')[:1]
        )
        return (
            Category.objects.filter(shayaris__approved=True)
            .distinct()
            .annotate(latest_shayari_at=Subquery(latest))
        )

    def location(self, item):
        return reverse('category', kwargs={'category_slug': item.slug})

    def lastmod(self, item):
        return item.latest_shayari_at


def sitemap_items():
    return {
        'static': StaticSitemap(),
        'categories': CategorySitemap(),
        'shayari': ShayariSitemap(),
    }
