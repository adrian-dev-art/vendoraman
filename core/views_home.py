from django.shortcuts import render
from .models import EventCategory


def home_view(request):
    categories = EventCategory.objects.all()
    return render(request, 'home.html', {'categories': categories})


def trust_guarantee_view(request):
    return render(request, 'trust_guarantee.html')
