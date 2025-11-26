"""
URL configuration for promise_tracker project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.urls import include, path

from promise_tracker.authentication import urls as authentication_urls
from promise_tracker.classifiers import urls as classifiers_urls
from promise_tracker.home import urls as home_urls
from promise_tracker.promises import urls as promises_urls
from promise_tracker.users import urls as users_urls

urlpatterns = i18n_patterns(
    path("", include(home_urls)),
    path("auth/", include(authentication_urls)),
    path("users/", include(users_urls)),
    path("promises/", include((promises_urls))),
    path("classifiers/", include(classifiers_urls)),
    path("i18n/", include("django.conf.urls.i18n")),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
