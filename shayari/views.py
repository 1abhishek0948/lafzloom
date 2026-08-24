from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.utils.http import url_has_allowed_host_and_scheme
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from .models import Shayari, Category
from .forms import ShayariForm
from lafzloom.translations import translate as t
from lafzloom.views import absolute_url


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

    page = Paginator(shayaris, 12).get_page(request.GET.get('page'))
    browse_is_indexable = not any(key in request.GET for key in ('q', 'author', 'category', 'sort'))
    canonical_path = reverse('shayari:list')
    if browse_is_indexable and request.GET.get('page'):
        canonical_path = f'{canonical_path}?page={request.GET["page"]}'
    context = {
        'seo_title': 'Browse Shayari and Poetry | Lafzloom',
        'seo_description': 'Browse shayari by title, author, category, language, or popularity on Lafzloom.',
        'seo_robots': 'index, follow' if browse_is_indexable else 'noindex, follow',
        'canonical_url': absolute_url(request, canonical_path),
        'seo_breadcrumbs': [{'name': 'Shayari', 'url': absolute_url(request, reverse('shayari:list')), 'position': 1}],
    }
    request.seo_overrides = context
    return render(
        request,
        'shayari/list.jinja',
        {
            'shayaris': page.object_list,
            'page_obj': page,
            'categories': categories,
            'query': query,
            'author_query': author,
            'sort': sort,
            'category_filter': category_filter,
            **context,
        },
    )


def category_legacy_redirect(request, category_slug):
    return redirect(f'{reverse("shayari:list")}?category={category_slug}')


def shayari_detail(request, pk):
    base_qs = Shayari.objects.select_related('author', 'category')
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        shayari = get_object_or_404(base_qs, pk=pk)
    elif request.user.is_authenticated:
        shayari = get_object_or_404(base_qs.filter(Q(approved=True) | Q(author=request.user)), pk=pk)
    else:
        shayari = get_object_or_404(base_qs, pk=pk, approved=True)
    description = ' '.join(shayari.text.split())
    if len(description) > 158:
        description = f'{description[:157].rsplit(" ", 1)[0]}…'
    canonical_url = absolute_url(request, reverse('shayari:detail', kwargs={'pk': shayari.pk}))
    breadcrumbs = [
        {'name': 'Shayari', 'url': absolute_url(request, reverse('shayari:list')), 'position': 1},
        {'name': shayari.category.name, 'url': absolute_url(request, reverse('category', kwargs={'category_slug': shayari.category.slug})), 'position': 2},
        {'name': shayari.title, 'url': canonical_url, 'position': 3},
    ]
    related_shayaris = (
        Shayari.objects.filter(approved=True, category=shayari.category)
        .exclude(pk=shayari.pk)
        .select_related('author', 'category')[:3]
    )
    request.seo_overrides = {
        'seo_title': f'{shayari.title} | {shayari.get_language_display()} Shayari | Lafzloom',
        'seo_description': description or f'Read {shayari.title} on Lafzloom.',
        'seo_author': shayari.author.username,
        'seo_robots': 'index, follow' if shayari.approved else 'noindex, nofollow',
        'canonical_url': canonical_url.replace('http://', 'https://', 1),
        'seo_og_type': 'article',
        'seo_og_locale': shayari.language,
        'seo_breadcrumbs': breadcrumbs,
        'seo_jsonld_extra': {
            '@context': 'https://schema.org',
            '@type': 'CreativeWork',
            'url': canonical_url.replace('http://', 'https://', 1),
            'headline': shayari.title,
            'text': shayari.text,
            'author': {'@type': 'Person', 'name': shayari.author.username},
            'datePublished': shayari.created_at.isoformat(),
            'dateModified': shayari.updated_at.isoformat(),
            'inLanguage': shayari.language,
            'isPartOf': {'@type': 'WebSite', 'name': 'Lafzloom'},
        },
    }
    return render(request, 'shayari/detail.jinja', {
        'shayari': shayari,
        'related_shayaris': related_shayaris,
    })


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
