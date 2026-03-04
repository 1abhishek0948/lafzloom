from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Shayari(models.Model):
    LANG_HI = 'hi'
    LANG_EN = 'en'
    LANG_UR = 'ur'
    LANG_CHOICES = [
        (LANG_HI, 'Hindi'),
        (LANG_EN, 'English'),
        (LANG_UR, 'Urdu'),
    ]

    title = models.CharField(max_length=200)
    text = models.TextField()
    language = models.CharField(max_length=2, choices=LANG_CHOICES, default=LANG_HI)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='shayaris')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shayaris')
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_shayaris', blank=True)
    saves = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='saved_shayaris', blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['approved', 'created_at']),
            models.Index(fields=['language']),
        ]

    def __str__(self):
        return f"{self.title} by {self.author}"

    @property
    def likes_count(self):
        return self.likes.count()

    @property
    def saves_count(self):
        return self.saves.count()
