from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import reverse
from django.shortcuts import render, get_object_or_404, redirect

from .models import Shayari, Category
from .forms import ShayariForm
from lafzverse.translations import translate as t


def home(request):
    categories = Category.objects.all()[:8]
    shayaris = (
        Shayari.objects.filter(approved=True)
        .select_related('author', 'category')
        .order_by('-created_at')[:6]
    )
    return render(request, 'home.jinja', {'categories': categories, 'shayaris': shayaris})


def shayari_list(request):
    shayaris = Shayari.objects.filter(approved=True).select_related('author', 'category')
    categories = Category.objects.all()

    query = request.GET.get('q', '')
    if query:
        shayaris = shayaris.filter(
            Q(title__icontains=query)
            | Q(text__icontains=query)
            | Q(author__username__icontains=query)
        )

    author = request.GET.get('author', '')
    if author:
        shayaris = shayaris.filter(author__username__icontains=author)

    category = request.GET.get('category', '')
    if category:
        shayaris = shayaris.filter(category__slug=category)
    category_filter = category

    sort = request.GET.get('sort', 'latest')
    if sort == 'popular':
        shayaris = shayaris.annotate(like_count=Count('likes')).order_by('-like_count', '-created_at')
    elif sort == 'oldest':
        shayaris = shayaris.order_by('created_at')
    else:
        shayaris = shayaris.order_by('-created_at')

    return render(
        request,
        'shayari/list.jinja',
        {
            'shayaris': shayaris,
            'categories': categories,
            'query': query,
            'author_query': author,
            'sort': sort,
            'category_filter': category_filter,
        },
    )


def category_legacy_redirect(request, category_slug):
    list_url = reverse('shayari:list')
    return redirect(f'{list_url}?category={category_slug}')


def shayari_detail(request, pk):
    base_qs = Shayari.objects.select_related('author', 'category')
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        shayari = get_object_or_404(base_qs, pk=pk)
    elif request.user.is_authenticated:
        shayari = get_object_or_404(base_qs.filter(Q(approved=True) | Q(author=request.user)), pk=pk)
    else:
        shayari = get_object_or_404(base_qs, pk=pk, approved=True)
    return render(request, 'shayari/detail.jinja', {'shayari': shayari})


def _can_manage_shayari(user, shayari):
    return user.is_authenticated and (
        user.is_staff or user.is_superuser or user == shayari.author
    )


@login_required
def submit_shayari(request):
    if request.method == 'POST':
        form = ShayariForm(request.POST)
        if form.is_valid():
            shayari = form.save(commit=False)
            shayari.author = request.user
            shayari.approved = True
            shayari.save()
            form.save_m2m()
            messages.success(request, t('Your verse is live!'))
            return redirect('shayari:detail', pk=shayari.pk)
    else:
        form = ShayariForm()
    return render(request, 'shayari/submit.jinja', {'form': form})


@login_required
def edit_shayari(request, pk):
    shayari = get_object_or_404(Shayari, pk=pk)
    if not _can_manage_shayari(request.user, shayari):
        return HttpResponseForbidden(t('You do not have permission to edit this shayari.'))
    if request.method == 'POST':
        form = ShayariForm(request.POST, instance=shayari)
        if form.is_valid():
            form.save()
            messages.success(request, t('Shayari updated.'))
            return redirect('shayari:detail', pk=shayari.pk)
    else:
        form = ShayariForm(instance=shayari)
    return render(request, 'shayari/edit.jinja', {'form': form, 'shayari': shayari})


@login_required
def delete_shayari(request, pk):
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid method')
    shayari = get_object_or_404(Shayari, pk=pk)
    if not _can_manage_shayari(request.user, shayari):
        return HttpResponseForbidden(t('You do not have permission to delete this shayari.'))
    shayari.delete()
    messages.success(request, t('Shayari deleted.'))
    next_url = request.POST.get('next', '')
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect('accounts:profile')


@login_required
def like_toggle(request, pk):
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid method')
    shayari = get_object_or_404(Shayari, pk=pk, approved=True)
    if request.user in shayari.likes.all():
        shayari.likes.remove(request.user)
        liked = False
    else:
        shayari.likes.add(request.user)
        liked = True
    return JsonResponse({'liked': liked, 'count': shayari.likes.count()})


@login_required
def save_toggle(request, pk):
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid method')
    shayari = get_object_or_404(Shayari, pk=pk, approved=True)
    if request.user in shayari.saves.all():
        shayari.saves.remove(request.user)
        saved = False
    else:
        shayari.saves.add(request.user)
        saved = True
    return JsonResponse({'saved': saved})
