from django.urls import include, path

from promise_tracker.promises.views.promises_views import (
    PromiseApproveView,
    PromiseCreateView,
    PromiseDeleteView,
    PromiseDetailView,
    PromiseEditView,
    PromiseListView,
    PromiseRejectView,
)

app_name = "promises"

promises_urlpatterns = [
    path("", PromiseListView.as_view(), name="list"),
    path("create/", PromiseCreateView.as_view(), name="create"),
    path("<uuid:id>/", PromiseDetailView.as_view(), name="details"),
    path("<uuid:id>/edit/", PromiseEditView.as_view(), name="edit"),
    path("<uuid:id>/approve/", PromiseApproveView.as_view(), name="approve"),
    path("<uuid:id>/reject/", PromiseRejectView.as_view(), name="reject"),
    path("<uuid:id>/delete/", PromiseDeleteView.as_view(), name="delete"),
]


urlpatterns = [
    path(
        "promises/",
        include((promises_urlpatterns, "promises"), namespace="promises"),
    ),
]
