from django.http import JsonResponse
from django.shortcuts import render


def about(request):
    return render(request, 'pages/about.jinja')


def contact(request):
    return render(request, 'pages/contact.jinja')


def privacy(request):
    return render(request, 'pages/privacy.jinja')


def terms(request):
    return render(request, 'pages/terms.jinja')


def healthz(request):
    return JsonResponse({'status': 'ok'})
