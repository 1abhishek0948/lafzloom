from rest_framework import serializers
from .models import Category, Shayari


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description')


class ShayariSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    likes_count = serializers.IntegerField(source='likes_count', read_only=True)
    saves_count = serializers.IntegerField(source='saves_count', read_only=True)

    class Meta:
        model = Shayari
        fields = (
            'id',
            'title',
            'text',
            'language',
            'category',
            'category_name',
            'author',
            'author_username',
            'approved',
            'created_at',
            'updated_at',
            'likes_count',
            'saves_count',
        )
        read_only_fields = ('author', 'approved', 'created_at', 'updated_at')


class ShayariAdminSerializer(ShayariSerializer):
    class Meta(ShayariSerializer.Meta):
        read_only_fields = ('author', 'created_at', 'updated_at')
