from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import View
from rolepermissions.roles import remove_role

from promise_tracker.common.mixins import RoleBasedAccessMixin, VerifiedLoginRequiredMixin
from promise_tracker.core.roles import RegisteredUser

from .factories import UnverifiedUserFactory, VerifiedUserFactory


class DummyView(VerifiedLoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("OK")


class DummyRoleView(RoleBasedAccessMixin, View):
    required_roles = [RegisteredUser]
    allow_guests = False

    def get(self, request, *args, **kwargs):
        return HttpResponse("OK")


class DummyRoleGuestView(RoleBasedAccessMixin, View):
    allow_guests = True

    def get(self, request, *args, **kwargs):
        return HttpResponse("OK")


class DummyRoleUnverifiedView(RoleBasedAccessMixin, View):
    required_roles = [RegisteredUser]
    allow_unverified = True

    def get(self, request, *args, **kwargs):
        return HttpResponse("OK")


class VerifiedLoginRequiredMixinTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.request.session = {}
        self.request._messages = FallbackStorage(self.request)

    def test_unauthenticated_redirects_to_login(self):
        request = self.request
        request.user = AnonymousUser()

        response = DummyView.as_view()(request)

        self.assertEqual(response.status_code, 302)
        self.assertIn(settings.LOGIN_URL, response.url)

    def test_unverified_user_redirects_to_verify(self):
        request = self.request
        request.user = UnverifiedUserFactory.create()

        response = DummyView.as_view()(self.request)

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("users:verify"), response.url)

    def test_verified_user_allows_access(self):
        request = self.request
        request.user = VerifiedUserFactory.create()

        response = DummyView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"OK")


class RoleBasedAccessMixinTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.request.session = {}
        self.request._messages = FallbackStorage(self.request)

    def test_guest_denied_when_allow_guests_false(self):
        request = self.request
        request.user = AnonymousUser()

        with self.assertRaises(PermissionDenied):
            DummyRoleView.as_view()(request)

        self.assertIn(_("Access denied!"), [m.message for m in request._messages])

    def test_guest_allowed_when_allow_guests_true(self):
        request = self.request
        request.user = AnonymousUser()

        response = DummyRoleGuestView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"OK")

    def test_user_with_required_role_has_access(self):
        request = self.request
        request.user = VerifiedUserFactory.create()

        response = DummyRoleView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"OK")

    def test_user_without_required_role_denied(self):
        request = self.request
        user = VerifiedUserFactory.create()
        remove_role(user, RegisteredUser)
        request.user = user

        with self.assertRaises(PermissionDenied):
            DummyRoleView.as_view()(request)

        self.assertIn(_("Access denied!"), [m.message for m in request._messages])

    def test_inactive_user_treated_as_guest_when_allow_guests_false(self):
        request = self.request
        request.user = VerifiedUserFactory.create(is_active=False)

        with self.assertRaises(PermissionDenied):
            DummyRoleView.as_view()(request)

        self.assertIn(_("Access denied!"), [m.message for m in request._messages])

    def test_inactive_user_treated_as_guest_when_allow_guests_true(self):
        request = self.request
        request.user = VerifiedUserFactory.create(is_active=False)

        response = DummyRoleGuestView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"OK")

    def test_unverified_user_treated_as_guest_when_allow_guests_false(self):
        request = self.request
        request.user = UnverifiedUserFactory.create()

        with self.assertRaises(PermissionDenied):
            DummyRoleView.as_view()(request)

        self.assertIn(_("Access denied!"), [m.message for m in request._messages])

    def test_unverified_user_allowed_when_allow_unverified_true(self):
        request = self.request
        request.user = UnverifiedUserFactory.create()

        response = DummyRoleUnverifiedView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"OK")

    def test_unverified_user_denied_when_allow_unverified_false(self):
        request = self.request
        request.user = UnverifiedUserFactory.create()

        with self.assertRaises(PermissionDenied):
            DummyRoleView.as_view()(request)

        self.assertIn(_("Access denied!"), [m.message for m in request._messages])
