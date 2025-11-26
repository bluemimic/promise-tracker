from django.urls import include, path

from promise_tracker.promises.views.analytics_views import AnalyticsView
from promise_tracker.promises.views.promise_results_views import (
    PromiseResultApproveView,
    PromiseResultCreateView,
    PromiseResultDeleteView,
    PromiseResultEditView,
    PromiseResultListView,
    PromiseResultMineListView,
    PromiseResultRejectView,
)
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
    path("<uuid:promise_id>/add/", PromiseResultCreateView.as_view(), name="create_result"),
    path("<uuid:promise_id>/<uuid:id>/edit/", PromiseResultEditView.as_view(), name="edit_result"),
    path("<uuid:promise_id>/<uuid:id>/approve/", PromiseResultApproveView.as_view(), name="approve_result"),
    path("<uuid:promise_id>/<uuid:id>/reject/", PromiseResultRejectView.as_view(), name="reject_result"),
    path("<uuid:promise_id>/<uuid:id>/delete/", PromiseResultDeleteView.as_view(), name="delete_result"),
]

promise_results_urlpatterns = [
    path("", PromiseResultListView.as_view(), name="list"),
    path("mine/", PromiseResultMineListView.as_view(), name="mine"),
]

promise_analytics_urlpatterns = [
    path("", AnalyticsView.as_view(), name="analytics"),
]

urlpatterns = [
    path(
        "promises/",
        include((promises_urlpatterns, "promises"), namespace="promises"),
    ),
    path(
        "results/",
        include((promise_results_urlpatterns, "promise_results"), namespace="promise_results"),
    ),
    path(
        "analytics/",
        include((promise_analytics_urlpatterns, "promise_analytics"), namespace="promise_analytics"),
    ),
]
