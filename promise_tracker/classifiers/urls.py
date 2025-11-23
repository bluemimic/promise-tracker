from django.urls import include, path

from promise_tracker.classifiers.views.convocation_views import (
    ConvocationCreateView,
    ConvocationDeleteView,
    ConvocationDetailView,
    ConvocationEditView,
    ConvocationListView,
)
from promise_tracker.classifiers.views.legislative_institution_views import (
    LegislativeInstitutionCreateView,
    LegislativeInstitutionDeleteView,
    LegislativeInstitutionDetailView,
    LegislativeInstitutionEditView,
    LegislativeInstitutionListView,
)
from promise_tracker.classifiers.views.political_party_views import (
    PoliticalPartyCreateView,
    PoliticalPartyDeleteView,
    PoliticalPartyDetailView,
    PoliticalPartyEditView,
    PoliticalPartyListView,
)
from promise_tracker.classifiers.views.political_union_views import (
    PoliticalUnionCreateView,
    PoliticalUnionDeleteView,
    PoliticalUnionDetailView,
    PoliticalUnionEditView,
    PoliticalUnionListView,
)

app_name = "classifiers"

legislative_institution_urlpatterns = [
    path("", LegislativeInstitutionListView.as_view(), name="list"),
    path("create/", LegislativeInstitutionCreateView.as_view(), name="create"),
    path("<uuid:id>/", LegislativeInstitutionDetailView.as_view(), name="detail"),
    path("<uuid:id>/edit/", LegislativeInstitutionEditView.as_view(), name="edit"),
    path("<uuid:id>/delete/", LegislativeInstitutionDeleteView.as_view(), name="delete"),
]

political_party_urlpatterns = [
    path("", PoliticalPartyListView.as_view(), name="list"),
    path("create/", PoliticalPartyCreateView.as_view(), name="create"),
    path("<uuid:id>/", PoliticalPartyDetailView.as_view(), name="detail"),
    path("<uuid:id>/edit/", PoliticalPartyEditView.as_view(), name="edit"),
    path("<uuid:id>/delete/", PoliticalPartyDeleteView.as_view(), name="delete"),
]

political_union_urlpatterns = [
    path("", PoliticalUnionListView.as_view(), name="list"),
    path("create/", PoliticalUnionCreateView.as_view(), name="create"),
    path("<uuid:id>/", PoliticalUnionDetailView.as_view(), name="detail"),
    path("<uuid:id>/edit/", PoliticalUnionEditView.as_view(), name="edit"),
    path("<uuid:id>/delete/", PoliticalUnionDeleteView.as_view(), name="delete"),
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
        "legislative-institutions/",
        include(
            (legislative_institution_urlpatterns, "legislative_institutions"), namespace="legislative_institutions"
        ),
    ),
    path(
        "political-parties/",
        include((political_party_urlpatterns, "political_parties"), namespace="political_parties"),
    ),
    path(
        "political-unions/",
        include((political_union_urlpatterns, "political_unions"), namespace="political_unions"),
    ),
    path(
        "convocations/",
        include((convocation_urlpatterns, "convocations"), namespace="convocations"),
    ),
]
