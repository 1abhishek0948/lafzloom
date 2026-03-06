from django.contrib import admin
from django import forms
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import path, reverse

from .models import Category, Shayari
from .importers import import_shayari_xlsx


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
    change_list_template = 'admin/shayari/shayari/change_list.html'

    class XlsxImportForm(forms.Form):
        xlsx_file = forms.FileField(
            required=True,
            widget=forms.ClearableFileInput(attrs={'accept': '.xlsx'}),
        )
        approve = forms.BooleanField(
            required=False,
            initial=True,
            label='Approve imported shayaris',
        )

    @admin.action(description='Approve selected shayaris')
    def approve_shayaris(self, request, queryset):
        queryset.update(approved=True)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'import-xlsx/',
                self.admin_site.admin_view(self.import_xlsx_view),
                name='shayari_shayari_import_xlsx',
            ),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['xlsx_import_form'] = self.XlsxImportForm()
        extra_context['xlsx_import_url'] = reverse('admin:shayari_shayari_import_xlsx')
        return super().changelist_view(request, extra_context=extra_context)

    def import_xlsx_view(self, request):
        if request.method != 'POST':
            return redirect('admin:shayari_shayari_changelist')

        form = self.XlsxImportForm(request.POST, request.FILES)
        if not form.is_valid():
            messages.error(request, 'Please upload a valid .xlsx file.')
            return redirect('admin:shayari_shayari_changelist')

        uploaded_file = form.cleaned_data['xlsx_file']
        if not uploaded_file.name.lower().endswith('.xlsx'):
            messages.error(request, 'Only .xlsx files are supported.')
            return redirect('admin:shayari_shayari_changelist')

        try:
            result = import_shayari_xlsx(
                uploaded_file,
                default_author=request.user,
                approve=form.cleaned_data.get('approve', False),
            )
        except Exception as exc:
            messages.error(request, f'Import failed: {exc}')
            return redirect('admin:shayari_shayari_changelist')

        if result.created:
            messages.success(request, f'Imported {result.created} shayari rows successfully.')
        if result.skipped:
            messages.warning(request, f'Skipped {result.skipped} row(s).')
        for warning in result.warnings[:10]:
            messages.warning(request, warning)
        if len(result.warnings) > 10:
            messages.warning(request, f'...and {len(result.warnings) - 10} more warnings.')

        return redirect('admin:shayari_shayari_changelist')
