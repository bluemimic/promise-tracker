from django.test import RequestFactory, TestCase
from django.utils import timezone
from faker import Faker

from promise_tracker.core.exceptions import ApplicationError, NotFoundError, PermissionViolationError
from promise_tracker.promises.models import Promise, PromiseResult
from promise_tracker.promises.selectors.promise_result_selectors import PromiseResultSelectors
from promise_tracker.promises.tests.factories import ValidPromiseFactory, ValidPromiseResultFactory
from promise_tracker.users.tests.factories import AdminUserFactory, VerifiedUserFactory

faker = Faker()


class PromiseResultSelectorsUnitTests(TestCase):
    def setUp(self):
        self.request = RequestFactory().get("/")
        self.request.user = VerifiedUserFactory.create()

    def test_get_results_raise_error_when_registered_is_unreviewed(self):
        selectors = PromiseResultSelectors(performed_by=VerifiedUserFactory.create())

        with self.assertRaises(PermissionViolationError):
            selectors.get_results(
                filters={
                    "is_mine": "true",
                    "is_unreviewed": "true",
                }
            )

    def test_get_results_raises_error_when_registered_without_is_mine(self):
        selectors = PromiseResultSelectors(performed_by=VerifiedUserFactory.create())

        with self.assertRaisesMessage(
            ApplicationError,
            str(selectors.REGISTERED_USER_ONLY_OWN_ERROR),
        ):
            selectors.get_results(filters={})

    def test_get_results_admin_returns_all(self):
        p1 = ValidPromiseResultFactory.create(
            review_status=PromiseResult.ReviewStatus.APPROVED,
            review_date=timezone.now() - timezone.timedelta(days=1),
        )
        p2 = ValidPromiseResultFactory.create(
            review_status=PromiseResult.ReviewStatus.PENDING,
        )
        p3 = ValidPromiseResultFactory.create(
            review_status=PromiseResult.ReviewStatus.REJECTED,
            review_date=timezone.now() - timezone.timedelta(days=2),
        )

        selectors = PromiseResultSelectors(performed_by=AdminUserFactory.create())

        qs = selectors.get_results(filters={})

        self.assertGreaterEqual(qs.count(), 3)
        ids = list(qs.values_list("id", flat=True))
        self.assertIn(p1.id, ids)
        self.assertIn(p2.id, ids)
        self.assertIn(p3.id, ids)

    def test_get_results_returns_all_mine_when_is_mine(self):
        user = VerifiedUserFactory.create()

        p1 = ValidPromiseResultFactory.create(
            created_by=user,
            review_status=Promise.ReviewStatus.PENDING,
        )
        p2 = ValidPromiseResultFactory.create(
            created_by=user,
            review_status=Promise.ReviewStatus.APPROVED,
            review_date=timezone.now() - timezone.timedelta(days=1),
        )

        selectors = PromiseResultSelectors(performed_by=user)

        qs = selectors.get_results(filters={"is_mine": True})
        ids = list(qs.values_list("id", flat=True))

        self.assertIn(p1.id, ids)
        self.assertIn(p2.id, ids)

    def test_get_results_returns_unreviewed_when_is_unreviewed(self):
        admin = AdminUserFactory.create()

        p1 = ValidPromiseResultFactory.create(
            review_status=PromiseResult.ReviewStatus.APPROVED,
            review_date=timezone.now() - timezone.timedelta(days=1),
        )

        p2 = ValidPromiseResultFactory.create(
            review_status=PromiseResult.ReviewStatus.PENDING,
        )

        self.request.user = admin
        selectors = PromiseResultSelectors(performed_by=admin)

        qs = selectors.get_results(filters={"is_unreviewed": True})
        ids = list(qs.values_list("id", flat=True))

        self.assertIn(p2.id, ids)
        self.assertNotIn(p1.id, ids)

    def test_get_results_by_promise_id_raises_not_found_when_promise_not_found(self):
        selectors = PromiseResultSelectors(performed_by=AdminUserFactory.create())

        with self.assertRaisesMessage(NotFoundError, str(selectors.NOT_FOUND_ERROR)):
            selectors.get_promise_results_by_promise_id(promise_id=faker.uuid4())

    def test_get_results_by_promise_id_returns_approved_when_guest(self):
        promise = ValidPromiseFactory.create(
            review_status=Promise.ReviewStatus.APPROVED,
            review_date=timezone.now() - timezone.timedelta(days=1),
        )
        p_approved = ValidPromiseResultFactory.create(
            promise=promise,
            review_status=PromiseResult.ReviewStatus.APPROVED,
            review_date=timezone.now() - timezone.timedelta(days=1),
        )
        p_pending = ValidPromiseResultFactory.create(
            promise=promise,
            review_status=PromiseResult.ReviewStatus.PENDING,
        )
        p_rejected = ValidPromiseResultFactory.create(
            promise=promise,
            review_status=PromiseResult.ReviewStatus.REJECTED,
            review_date=timezone.now() - timezone.timedelta(days=2),
        )

        selectors = PromiseResultSelectors(performed_by=None)

        qs = selectors.get_promise_results_by_promise_id(promise_id=promise.id)
        ids = list(qs.values_list("id", flat=True))

        self.assertIn(p_approved.id, ids)
        self.assertNotIn(p_pending.id, ids)
        self.assertNotIn(p_rejected.id, ids)

    def test_get_results_by_promise_id_returns_approved_and_own_when_registered(self):
        user = VerifiedUserFactory.create()

        promise = ValidPromiseFactory.create(
            review_status=Promise.ReviewStatus.APPROVED,
            review_date=timezone.now() - timezone.timedelta(days=1),
        )
        p_user_pending = ValidPromiseResultFactory.create(
            promise=promise,
            created_by=user,
            review_status=PromiseResult.ReviewStatus.PENDING,
        )
        p_user_rejected = ValidPromiseResultFactory.create(
            promise=promise,
            created_by=user,
            review_status=PromiseResult.ReviewStatus.REJECTED,
            review_date=timezone.now() - timezone.timedelta(days=2),
        )
        p_other_approved = ValidPromiseResultFactory.create(
            promise=promise,
            review_status=PromiseResult.ReviewStatus.APPROVED,
            review_date=timezone.now() - timezone.timedelta(days=1),
        )
        p_other_pending = ValidPromiseResultFactory.create(
            promise=promise,
            review_status=PromiseResult.ReviewStatus.PENDING,
        )

        selectors = PromiseResultSelectors(performed_by=user)

        qs = selectors.get_promise_results_by_promise_id(promise_id=promise.id)
        ids = list(qs.values_list("id", flat=True))

        self.assertIn(p_user_pending.id, ids)
        self.assertIn(p_user_rejected.id, ids)
        self.assertIn(p_other_approved.id, ids)
        self.assertNotIn(p_other_pending.id, ids)

    def test_get_results_by_promise_id_returns_all_when_admin(self):
        admin = AdminUserFactory.create()

        promise = ValidPromiseFactory.create(
            review_status=Promise.ReviewStatus.APPROVED,
            review_date=timezone.now() - timezone.timedelta(days=1),
        )
        p_approved = ValidPromiseResultFactory.create(
            promise=promise,
            created_by=VerifiedUserFactory.create(),
            review_status=PromiseResult.ReviewStatus.APPROVED,
            review_date=timezone.now() - timezone.timedelta(days=1),
        )
        p_rejected = ValidPromiseResultFactory.create(
            promise=promise,
            created_by=VerifiedUserFactory.create(),
            review_status=PromiseResult.ReviewStatus.REJECTED,
            review_date=timezone.now() - timezone.timedelta(days=2),
        )
        p_pending = ValidPromiseResultFactory.create(
            promise=promise,
            created_by=VerifiedUserFactory.create(),
            review_status=PromiseResult.ReviewStatus.PENDING,
        )

        selectors = PromiseResultSelectors(performed_by=admin)

        qs = selectors.get_promise_results_by_promise_id(promise_id=promise.id)
        ids = list(qs.values_list("id", flat=True))

        self.assertIn(p_approved.id, ids)
        self.assertIn(p_pending.id, ids)
        self.assertIn(p_rejected.id, ids)
