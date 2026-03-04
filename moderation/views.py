from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

from shayari.forms import ShayariForm
from shayari.models import Shayari
from lafzverse.translations import translate as t


@staff_member_required(login_url='accounts:login')
def pending(request):
    shayaris = Shayari.objects.select_related('author', 'category').order_by('-created_at')
    return render(request, 'moderation/pending.jinja', {'shayaris': shayaris})


@staff_member_required(login_url='accounts:login')
def approve(request, pk):
    if request.method == 'POST':
        shayari = get_object_or_404(Shayari, pk=pk)
        shayari.approved = True
        shayari.save(update_fields=['approved'])
        messages.success(request, t('Shayari published.'))
    return redirect('moderation:pending')


@staff_member_required(login_url='accounts:login')
def unpublish(request, pk):
    if request.method == 'POST':
        shayari = get_object_or_404(Shayari, pk=pk)
        shayari.approved = False
        shayari.save(update_fields=['approved'])
        messages.success(request, t('Shayari hidden from public view.'))
    return redirect('moderation:pending')


@staff_member_required(login_url='accounts:login')
def reject(request, pk):
    if request.method == 'POST':
        shayari = get_object_or_404(Shayari, pk=pk)
        shayari.delete()
        messages.success(request, t('Shayari removed.'))
    return redirect('moderation:pending')


@staff_member_required(login_url='accounts:login')
def edit(request, pk):
    shayari = get_object_or_404(Shayari, pk=pk)
    if request.method == 'POST':
        form = ShayariForm(request.POST, instance=shayari)
        if form.is_valid():
            form.save()
            messages.success(request, t('Shayari updated.'))
            return redirect('moderation:pending')
    else:
        form = ShayariForm(instance=shayari)
    return render(request, 'moderation/edit.jinja', {'form': form, 'shayari': shayari})
