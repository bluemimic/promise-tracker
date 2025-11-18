from django.shortcuts import render


def index(request):
    """Simple home page view used as `home:index` in templates."""
    return render(request, "home/index.html", {})
