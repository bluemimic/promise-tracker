from django.test import TestCase, tag
from faker import Faker

from promise_tracker.core.exceptions import NotFoundError, PermissionViolationError
from promise_tracker.users.selectors import UserSelectors
from promise_tracker.users.tests.factories import AdminUserFactory, VerifiedUserFactory

faker = Faker()


class UserSelectorsUnitTests(TestCase):
    def setUp(self):
        method = getattr(self, self._testMethodName)

        tags = getattr(method, "tags", {})
        if "skip_setup" in tags:
            return

        self.service = UserSelectors(performed_by=AdminUserFactory.create())
        self.registered_user_service = UserSelectors(performed_by=VerifiedUserFactory.create())

    def test_get_user_by_id_raises_error_when_not_found(self):
        with self.assertRaisesMessage(NotFoundError, str(self.service.NOT_FOUND_ERROR)):
            self.service.get_user_by_id(id=faker.uuid4())

    def test_get_user_by_id_raises_error_when_is_registered_but_not_owner(self):
        user = VerifiedUserFactory.create()
        other_user = VerifiedUserFactory.create()

        registered_user_service = UserSelectors(performed_by=user)

        with self.assertRaises(PermissionViolationError):
            registered_user_service.get_user_by_id(id=other_user.id)

    def test_get_user_by_id_raises_error_when_is_registered_and_inactive(self):
        user = VerifiedUserFactory.create(is_active=False)

        service = UserSelectors(performed_by=user)

        with self.assertRaises(PermissionViolationError):
            service.get_user_by_id(id=user.id)

    def test_get_user_by_id_raises_error_when_is_registered_and_deleted(self):
        user = VerifiedUserFactory.create(is_deleted=True)

        service = UserSelectors(performed_by=user)

        with self.assertRaisesMessage(NotFoundError, str(self.service.NOT_FOUND_ERROR)):
            service.get_user_by_id(id=user.id)

    def test_get_user_by_id_returns_user_when_allowed(self):
        fetched = self.registered_user_service.get_user_by_id(id=self.registered_user_service.performed_by.id)

        self.assertEqual(fetched.id, self.registered_user_service.performed_by.id)

    @tag("skip_setup")
    def test_get_users_returns_all_when_no_filters(self):
        u1 = AdminUserFactory.create()
        u2 = VerifiedUserFactory.create()

        service = UserSelectors(performed_by=u1)

        qs = service.get_users(filters={})

        ids = list(qs.values_list("id", flat=True))
        self.assertIn(u1.id, ids)
        self.assertIn(u2.id, ids)

    @tag("skip_setup")
    def test_get_users_applies_filters(self):
        u1 = AdminUserFactory.create(name="Alice")
        u2 = VerifiedUserFactory.create(name="Bob")

        service = UserSelectors(performed_by=u1)

        qs = service.get_users(filters={"name__icontains": "Alice"})

        ids = list(qs.values_list("id", flat=True))
        self.assertIn(u1.id, ids)
        self.assertNotIn(u2.id, ids)

    @tag("skip_setup")
    def test_get_users_returns_none_when_no_match(self):
        u1 = AdminUserFactory.create(name="Alice")
        VerifiedUserFactory.create(name="Bob")

        service = UserSelectors(performed_by=u1)

        qs = service.get_users(filters={"name__icontains": "Charlie"})

        self.assertEqual(qs.count(), 0)
