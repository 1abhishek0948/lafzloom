from django.contrib import admin
from .models import Category, Shayari


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Shayari)
class ShayariAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'language', 'approved', 'created_at')
    list_filter = ('approved', 'language', 'category')
    search_fields = ('title', 'text', 'author__username')
    actions = ['approve_shayaris']

    @admin.action(description='Approve selected shayaris')
    def approve_shayaris(self, request, queryset):
        queryset.update(approved=True)
