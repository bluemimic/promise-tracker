from django.urls import include, path

from promise_tracker.classifiers.views.convocation_views import (
    ConvocationCreateView,
    ConvocationDeleteView,
    ConvocationDetailView,
    ConvocationEditView,
    ConvocationListView,
)
from promise_tracker.classifiers.views.political_party_views import (
    PoliticalPartyCreateView,
    PoliticalPartyDeleteView,
    PoliticalPartyDetailView,
    PoliticalPartyEditView,
    PoliticalPartyListView,
)

app_name = "classifiers"

political_party_urlpatterns = [
    path("", PoliticalPartyListView.as_view(), name="list"),
    path("create/", PoliticalPartyCreateView.as_view(), name="create"),
    path("<uuid:id>/", PoliticalPartyDetailView.as_view(), name="detail"),
    path("<uuid:id>/edit/", PoliticalPartyEditView.as_view(), name="edit"),
    path("<uuid:id>/delete/", PoliticalPartyDeleteView.as_view(), name="delete"),
]

convocation_urlpatterns = [
    path("", ConvocationListView.as_view(), name="list"),
    path("create/", ConvocationCreateView.as_view(), name="create"),
    path("<uuid:id>/", ConvocationDetailView.as_view(), name="detail"),
    path("<uuid:id>/edit/", ConvocationEditView.as_view(), name="edit"),
    path("<uuid:id>/delete/", ConvocationDeleteView.as_view(), name="delete"),
]


urlpatterns = [
    path(
        "political-parties/",
        include((political_party_urlpatterns, "political_parties"), namespace="political_parties"),
    ),
    path(
        "convocations/",
        include((convocation_urlpatterns, "convocations"), namespace="convocations"),
    ),
]
