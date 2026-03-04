from django import forms
from .models import Shayari


class ShayariForm(forms.ModelForm):
    class Meta:
        model = Shayari
        fields = ('title', 'text', 'language', 'category')
        widgets = {
            'text': forms.Textarea(attrs={'rows': 6}),
        }
