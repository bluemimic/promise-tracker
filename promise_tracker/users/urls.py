from django.urls import path

from .views import (
    UserBlockView,
    UserCreateView,
    UserDeleteView,
    UserDetailView,
    UserEditView,
    UserListView,
    UserResendVerificationView,
    UserUnblockView,
    UserVerifyView,
)

app_name = "users"

urlpatterns = [
    path("", UserListView.as_view(), name="list"),
    path("create/", UserCreateView.as_view(), name="create"),
    path("<uuid:id>/", UserDetailView.as_view(), name="detail"),
    path("<uuid:id>/edit/", UserEditView.as_view(), name="edit"),
    path("<uuid:id>/delete/", UserDeleteView.as_view(), name="delete"),
    path("verify/", UserVerifyView.as_view(), name="verify"),
    path("resend-verification/", UserResendVerificationView.as_view(), name="resend_verification"),
    path("<uuid:id>/block/", UserBlockView.as_view(), name="block"),
    path("<uuid:id>/unblock/", UserUnblockView.as_view(), name="unblock"),
]
