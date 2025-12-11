from django.test import RequestFactory, TestCase
from django.utils import timezone
from faker import Faker

from promise_tracker.classifiers.tests.factories import ValidPoliticalPartyFactory
from promise_tracker.core.exceptions import NotFoundError
from promise_tracker.promises.models import Promise, PromiseResult
from promise_tracker.promises.selectors.analytics_selectors import AnalyticsSelectors
from promise_tracker.promises.tests.factories import ValidPromiseFactory, ValidPromiseResultFactory
from promise_tracker.users.tests.factories import VerifiedUserFactory

faker = Faker()


class AnalyticsSelectorsUnitTests(TestCase):
    def setUp(self):
        self.request = RequestFactory().get("/")
        self.request.user = VerifiedUserFactory.create()

    def test_get_analytics_reaise_error_when_party_not_found(self):
        selectors = AnalyticsSelectors()

        with self.assertRaisesMessage(
            NotFoundError,
            str(selectors.PARTY_NOT_FOUND),
        ):
            selectors.get_analytics(
                filters={
                    "party": faker.uuid4(),
                }
            )

    def test_get_analytics_returns_empty_when_no_results(self):
        selectors = AnalyticsSelectors()

        analytics = selectors.get_analytics(filters={})

        self.assertEqual(len(analytics), 0)

    def test_get_analytics_returns_correct_counts_when_party_is_selected(self):
        party = ValidPoliticalPartyFactory.create()

        promise = ValidPromiseFactory.create(
            party=party,
            review_status=Promise.ReviewStatus.APPROVED,
            review_date=timezone.now() - timezone.timedelta(days=2),
        )

        ValidPromiseResultFactory.create(
            promise=promise,
            status=PromiseResult.CompletionStatus.COMPLETED,
            review_status=PromiseResult.ReviewStatus.APPROVED,
            review_date=timezone.now() - timezone.timedelta(days=1),
            is_final=True,
        )
        ValidPromiseResultFactory.create(
            promise=promise,
            status=PromiseResult.CompletionStatus.ABANDONED,
            review_status=PromiseResult.ReviewStatus.APPROVED,
            review_date=timezone.now() - timezone.timedelta(days=1),
            is_final=True,
        )
        ValidPromiseResultFactory.create(
            promise=promise,
            status=PromiseResult.CompletionStatus.COMPLETED,
            review_status=PromiseResult.ReviewStatus.PENDING,
            is_final=True,
        )

        selectors = AnalyticsSelectors()

        analytics = selectors.get_analytics(
            filters={
                "party_id": party.id,
            }
        )

        self.assertEqual(len(analytics), 1)
        record = analytics[0]
        self.assertEqual(record.id, party.id)
        self.assertEqual(record.name, party.name)
        self.assertEqual(record.completed_count, 1)
        self.assertEqual(record.uncompleted_count, 1)

    def test_get_analytics_returns_correct_counts_when_no_party_selected(self):
        party1 = ValidPoliticalPartyFactory.create()
        party2 = ValidPoliticalPartyFactory.create()

        promise1 = ValidPromiseFactory.create(
            party=party1,
            review_status=Promise.ReviewStatus.APPROVED,
            review_date=timezone.now() - timezone.timedelta(days=2),
        )

        promise2 = ValidPromiseFactory.create(
            party=party2,
            review_status=Promise.ReviewStatus.APPROVED,
            review_date=timezone.now() - timezone.timedelta(days=2),
        )

        ValidPromiseResultFactory.create(
            promise=promise1,
            status=PromiseResult.CompletionStatus.COMPLETED,
            review_status=PromiseResult.ReviewStatus.APPROVED,
            review_date=timezone.now() - timezone.timedelta(days=1),
            is_final=True,
        )

        ValidPromiseResultFactory.create(
            promise=promise1,
            status=PromiseResult.CompletionStatus.ABANDONED,
            review_status=PromiseResult.ReviewStatus.APPROVED,
            review_date=timezone.now() - timezone.timedelta(days=1),
            is_final=True,
        )

        ValidPromiseResultFactory.create(
            promise=promise2,
            status=PromiseResult.CompletionStatus.COMPLETED,
            review_status=PromiseResult.ReviewStatus.APPROVED,
            review_date=timezone.now() - timezone.timedelta(days=1),
            is_final=True,
        )

        selectors = AnalyticsSelectors()

        analytics = selectors.get_analytics(filters={})

        self.assertEqual(len(analytics), 2)

        record1 = next((a for a in analytics if a.id == party1.id), None)

        self.assertIsNotNone(record1)
        self.assertEqual(record1.completed_count, 1)
        self.assertEqual(record1.uncompleted_count, 1)

        record2 = next((a for a in analytics if a.id == party2.id), None)

        self.assertIsNotNone(record2)
        self.assertEqual(record2.completed_count, 1)
        self.assertEqual(record2.uncompleted_count, 0)
