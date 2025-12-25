from django.test import RequestFactory, TestCase
from django.utils import timezone
from faker import Faker

from promise_tracker.core.exceptions import ApplicationError, NotFoundError, PermissionViolationError
from promise_tracker.promises.models import Promise, PromiseResult
from promise_tracker.promises.selectors.promise_selectors import PromiseSelectors
from promise_tracker.promises.tests.factories import ValidPromiseFactory, ValidPromiseResultFactory
from promise_tracker.users.tests.factories import AdminUserFactory, VerifiedUserFactory

faker = Faker()


class PromiseSelectorsUnitTests(TestCase):
    def setUp(self):
        self.request = RequestFactory().get("/")
        self.request.user = VerifiedUserFactory.create()

    def test_get_promises_mine_for_guest_raises(self):
        selectors = PromiseSelectors(request=self.request, performed_by=None)

        with self.assertRaisesMessage(
            ApplicationError,
            str(selectors.USER_IS_NOT_REGISTERED_ERROR),
        ):
            selectors.get_promises(filters={"is_mine": "true"})

    def test_get_promises_unreviewed_for_non_admin_raises(self):
        selectors = PromiseSelectors(request=self.request, performed_by=VerifiedUserFactory.create())

        with self.assertRaises(PermissionViolationError):
            selectors.get_promises(filters={"is_unreviewed": "true"})

    def test_get_promises_admin_returns_all(self):
        p1 = ValidPromiseFactory.create(
            review_status=Promise.ReviewStatus.APPROVED,
            review_date=timezone.now() - timezone.timedelta(days=1),
        )
        p2 = ValidPromiseFactory.create(
            review_status=Promise.ReviewStatus.PENDING,
        )
        p3 = ValidPromiseFactory.create(
            review_status=Promise.ReviewStatus.REJECTED,
            review_date=timezone.now() - timezone.timedelta(days=2),
        )

        selectors = PromiseSelectors(request=self.request, performed_by=AdminUserFactory.create())

        qs = selectors.get_promises(filters={})

        self.assertGreaterEqual(qs.count(), 3)
        ids = list(qs.values_list("id", flat=True))
        self.assertIn(p1.id, ids)
        self.assertIn(p2.id, ids)
        self.assertIn(p3.id, ids)

    def test_get_promises_guest_returns_only_approved(self):
        p_approved = ValidPromiseFactory.create(
            review_status=Promise.ReviewStatus.APPROVED,
            review_date=timezone.now() - timezone.timedelta(days=1),
        )
        p_pending = ValidPromiseFactory.create(review_status=Promise.ReviewStatus.PENDING)

        selectors = PromiseSelectors(request=self.request, performed_by=None)

        qs = selectors.get_promises(filters={})

        ids = list(qs.values_list("id", flat=True))
        self.assertIn(p_approved.id, ids)
        self.assertNotIn(p_pending.id, ids)

    def test_get_promises_registered_is_mine_true_returns_only_user_promises(self):
        user = VerifiedUserFactory.create()
        other = VerifiedUserFactory.create()

        p1 = ValidPromiseFactory.create(created_by=user, review_status=Promise.ReviewStatus.PENDING)
        p2 = ValidPromiseFactory.create(
            created_by=user,
            review_status=Promise.ReviewStatus.APPROVED,
            review_date=timezone.now() - timezone.timedelta(days=1),
        )
        p3 = ValidPromiseFactory.create(created_by=other, review_status=Promise.ReviewStatus.PENDING)

        self.request.user = user
        selectors = PromiseSelectors(request=self.request, performed_by=user)

        qs = selectors.get_promises(filters={"is_mine": "true"})
        ids = list(qs.values_list("id", flat=True))

        self.assertIn(p1.id, ids)
        self.assertIn(p2.id, ids)
        self.assertNotIn(p3.id, ids)

    def test_get_promises_registered_without_is_mine_returns_approved_or_created_by_user(self):
        user = VerifiedUserFactory.create()
        other = VerifiedUserFactory.create()

        p_user_pending = ValidPromiseFactory.create(created_by=user, review_status=Promise.ReviewStatus.PENDING)
        p_other_approved = ValidPromiseFactory.create(
            created_by=other,
            review_status=Promise.ReviewStatus.APPROVED,
            review_date=timezone.now() - timezone.timedelta(days=1),
        )
        p_other_pending = ValidPromiseFactory.create(created_by=other, review_status=Promise.ReviewStatus.PENDING)

        selectors = PromiseSelectors(request=self.request, performed_by=user)

        qs = selectors.get_promises(filters={})
        ids = list(qs.values_list("id", flat=True))

        self.assertIn(p_user_pending.id, ids)
        self.assertIn(p_other_approved.id, ids)
        self.assertNotIn(p_other_pending.id, ids)

    def test_get_promises_admin_unreviewed(self):
        admin = AdminUserFactory.create()

        p1 = ValidPromiseFactory.create(
            name="1",
            results=[],
            review_status=Promise.ReviewStatus.APPROVED,
            review_date=timezone.now() - timezone.timedelta(days=1),
        )

        ValidPromiseResultFactory.create(
            promise=p1,
            is_final=True,
            review_status=Promise.ReviewStatus.APPROVED,
            review_date=timezone.now() - timezone.timedelta(days=1),
            status=PromiseResult.CompletionStatus.COMPLETED,
        )

        p2 = ValidPromiseFactory.create(
            name="2",
            review_status=Promise.ReviewStatus.PENDING,
        )

        self.request.user = admin
        selectors = PromiseSelectors(request=self.request, performed_by=admin)

        qs_name = selectors.get_promises(filters={"name": "1"})
        self.assertEqual(1, qs_name.count())
        self.assertTrue(any(p.id == p1.id for p in qs_name))

        qs_result = selectors.get_promises(filters={"result_status": PromiseResult.CompletionStatus.COMPLETED})
        ids_result = list(qs_result.values_list("id", flat=True))
        self.assertEqual(1, len(ids_result))
        self.assertIn(p1.id, ids_result)

        qs_unrev = selectors.get_promises(filters={"is_unreviewed": True})
        ids_unrev = list(qs_unrev.values_list("id", flat=True))
        self.assertEqual(1, len(ids_unrev))
        self.assertIn(p2.id, ids_unrev)

    def test_get_promise_by_id_raises_not_found(self):
        selectors = PromiseSelectors(request=self.request, performed_by=AdminUserFactory.create())

        with self.assertRaisesMessage(NotFoundError, str(selectors.NOT_FOUND_ERROR)):
            selectors.get_promise_by_id(id=faker.uuid4())

    def test_get_promise_by_id_returns_promise_when_allowed(self):
        promise = ValidPromiseFactory.create()

        selectors = PromiseSelectors(request=self.request, performed_by=AdminUserFactory.create())

        fetched = selectors.get_promise_by_id(id=promise.id)

        self.assertEqual(fetched.id, promise.id)

    def test_get_promise_by_id_raises_permission_violation_when_not_allowed(self):
        user = VerifiedUserFactory.create()
        promise = ValidPromiseFactory.create(
            created_by=VerifiedUserFactory.create(),
            review_status=Promise.ReviewStatus.PENDING,
        )

        selectors = PromiseSelectors(request=self.request, performed_by=user)

        with self.assertRaisesMessage(PermissionViolationError, ""):
            selectors.get_promise_by_id(id=promise.id)
