from datetime import timedelta
from unittest.mock import MagicMock

from django.test import RequestFactory, TestCase
from django.utils import timezone
from faker import Faker

from promise_tracker.classifiers.tests.factories import ValidConvocationFactory, ValidPoliticalPartyFactory
from promise_tracker.core.exceptions import ApplicationError, NotFoundError, PermissionViolationError
from promise_tracker.promises.models import Promise
from promise_tracker.promises.services.promise_services import PromiseService
from promise_tracker.promises.tests.factories import ValidPromiseFactory, ValidPromiseResultFactory
from promise_tracker.users.models import BaseUser
from promise_tracker.users.tests.factories import AdminUserFactory, VerifiedUserFactory

faker = Faker()


class PromiseServicesUnitTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.mock_base_service = MagicMock()

        self.mocked_service = PromiseService(
            performed_by=MagicMock(spec=BaseUser),
            base_service=self.mock_base_service,
        )

        self.service = PromiseService(
            performed_by=AdminUserFactory.create(),
        )

    def test_create_raises_date_in_future(self):
        promise = ValidPromiseFactory.create(
            date=faker.date_between(start_date="+1d", end_date="+10d"),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.DATE_IN_FUTURE),
        ):
            self.mocked_service.create_promise(
                name=faker.word(),
                description=promise.description,
                sources=promise.sources,
                date=promise.date,
                party_id=promise.party.id,
                convocation_id=promise.convocation.id,
            )

    def test_create_raises_party_not_found(self):
        promise = ValidPromiseFactory.create()

        with self.assertRaisesMessage(
            NotFoundError,
            str(self.mocked_service.PARTY_NOT_FOUND),
        ):
            self.mocked_service.create_promise(
                name=faker.word(),
                description=promise.description,
                sources=promise.sources,
                date=promise.date,
                party_id=faker.uuid4(),
                convocation_id=promise.convocation.id,
            )

    def test_create_raises_convocation_not_found(self):
        promise = ValidPromiseFactory.create()

        with self.assertRaisesMessage(
            NotFoundError,
            str(self.mocked_service.CONVOCATION_NOT_FOUND),
        ):
            self.mocked_service.create_promise(
                name=promise.name,
                description=promise.description,
                sources=promise.sources,
                date=promise.date,
                party_id=promise.party.id,
                convocation_id=faker.uuid4(),
            )

    def test_create_raises_party_not_elected_in_convocation(self):
        promise = ValidPromiseFactory.create()
        convocation = ValidConvocationFactory.create()
        party = ValidPoliticalPartyFactory.create()

        with self.assertRaisesMessage(
            ApplicationError,
            str(
                self.mocked_service.PARTY_NOT_ELECTED_IN_CONVOCATION.format(
                    name=party.name,
                    convocation=convocation.name,
                )
            ),
        ):
            self.mocked_service.create_promise(
                name=promise.name,
                description=promise.description,
                sources=promise.sources,
                date=promise.date,
                party_id=party.id,
                convocation_id=convocation.id,
            )

    def test_create_raises_when_promise_with_same_name_exists(self):
        existing = ValidPromiseFactory.create()

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.service.UNIQUE_CONSTRAINT_MESSAGE.format(name=existing.name)),
        ):
            self.service.create_promise(
                name=existing.name,
                description=existing.description,
                sources=existing.sources,
                date=existing.date,
                party_id=existing.party.id,
                convocation_id=existing.convocation.id,
            )

    def test_create_raises_error_when_party_established_after_promise_date(self):
        convocation = ValidConvocationFactory.create()

        promise = ValidPromiseFactory.create(
            date=faker.date_between(
                start_date="-10y",
                end_date=convocation.political_parties.first().established_date,
            ),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(
                self.mocked_service.ESTABLISHED_DATE_LATER_THAN_PROMISE.format(
                    name=convocation.political_parties.first().name
                )
            ),
        ):
            self.mocked_service.create_promise(
                name=faker.word(),
                description=promise.description,
                sources=promise.sources,
                date=promise.date,
                party_id=convocation.political_parties.first().id,
                convocation_id=convocation.id,
            )

    def test_create_raises_error_when_party_liquidated_before_promise_date(self):
        convocation = ValidConvocationFactory.create()

        ld = convocation.political_parties.first().liquidated_date
        start = ld + timedelta(days=1) if ld is not None else "-1y"

        promise = ValidPromiseFactory.create(
            date=faker.date_between(start_date=start, end_date="today"),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(
                self.mocked_service.LIQIDATED_DATE_EARLIER_THAN_PROMISE.format(
                    name=convocation.political_parties.first().name
                )
            ),
        ):
            self.mocked_service.create_promise(
                name=faker.word(),
                description=promise.description,
                sources=promise.sources,
                date=promise.date,
                party_id=convocation.political_parties.first().id,
                convocation_id=convocation.id,
            )

    def test_update_raises_error_when_promise_not_found(self):
        promise = ValidPromiseFactory.create()

        with self.assertRaisesMessage(
            NotFoundError,
            str(self.mocked_service.NOT_FOUND_MESSAGE),
        ):
            self.mocked_service.edit_promise(
                id=faker.uuid4(),
                name=faker.word(),
                description=promise.description,
                sources=promise.sources,
                date=promise.date,
                party_id=promise.party.id,
                convocation_id=promise.convocation.id,
            )

    def test_update_raises_error_when_user_is_not_owner_or_admin(self):
        author = VerifiedUserFactory.create()

        existing_promise = ValidPromiseFactory.create(created_by=author)

        non_author_user = VerifiedUserFactory.create()
        service = PromiseService(
            performed_by=non_author_user,
        )

        with self.assertRaises(PermissionViolationError):
            service.edit_promise(
                id=existing_promise.id,
                name=existing_promise.name,
                description=existing_promise.description,
                sources=existing_promise.sources,
                date=existing_promise.date,
                party_id=existing_promise.party.id,
                convocation_id=existing_promise.convocation.id,
            )

    def test_update_can_access_if_admin(self):
        author = VerifiedUserFactory.create()

        existing_promise = ValidPromiseFactory.create(created_by=author)

        admin_user = AdminUserFactory.create()
        service = PromiseService(
            performed_by=admin_user,
        )

        try:
            service.edit_promise(
                id=existing_promise.id,
                name=existing_promise.name,
                description=existing_promise.description,
                sources=existing_promise.sources,
                date=existing_promise.date,
                party_id=existing_promise.party.id,
                convocation_id=existing_promise.convocation.id,
            )
        except PermissionViolationError:
            self.fail("edit_promise() raised PermissionViolationError unexpectedly for admin user!")

    def test_update_raises_error_when_status_is_not_pending(self):
        promise = ValidPromiseFactory.create(
            review_status=Promise.ReviewStatus.APPROVED,
            review_date=timezone.make_aware(faker.date_time_this_year()),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.CANNOT_EDIT_REVIEWED),
        ):
            self.mocked_service.edit_promise(
                id=promise.id,
                name=faker.word(),
                description=promise.description,
                sources=promise.sources,
                date=promise.date,
                party_id=promise.party.id,
                convocation_id=promise.convocation.id,
            )

    def test_update_raises_error_when_established_date_in_future(self):
        promise = ValidPromiseFactory.create(
            date=faker.date_between(start_date="+1d", end_date="+10d"),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.DATE_IN_FUTURE),
        ):
            self.mocked_service.edit_promise(
                id=promise.id,
                name=faker.word(),
                description=promise.description,
                sources=promise.sources,
                date=promise.date,
                party_id=promise.party.id,
                convocation_id=promise.convocation.id,
            )

    def test_update_raises_party_not_found(self):
        promise = ValidPromiseFactory.create()

        with self.assertRaisesMessage(
            NotFoundError,
            str(self.mocked_service.PARTY_NOT_FOUND),
        ):
            self.mocked_service.edit_promise(
                id=promise.id,
                name=faker.word(),
                description=promise.description,
                sources=promise.sources,
                date=promise.date,
                party_id=faker.uuid4(),
                convocation_id=promise.convocation.id,
            )

    def test_update_raises_convocation_not_found(self):
        promise = ValidPromiseFactory.create()

        with self.assertRaisesMessage(
            NotFoundError,
            str(self.mocked_service.CONVOCATION_NOT_FOUND),
        ):
            self.mocked_service.edit_promise(
                id=promise.id,
                name=faker.word(),
                description=promise.description,
                sources=promise.sources,
                date=promise.date,
                party_id=promise.party.id,
                convocation_id=faker.uuid4(),
            )

    def test_update_raises_party_not_elected_in_convocation(self):
        promise = ValidPromiseFactory.create()
        convocation = ValidConvocationFactory.create()
        party = ValidPoliticalPartyFactory.create()

        with self.assertRaisesMessage(
            ApplicationError,
            str(
                self.mocked_service.PARTY_NOT_ELECTED_IN_CONVOCATION.format(
                    name=party.name,
                    convocation=convocation.name,
                )
            ),
        ):
            self.mocked_service.edit_promise(
                id=promise.id,
                name=promise.name,
                description=promise.description,
                sources=promise.sources,
                date=promise.date,
                party_id=party.id,
                convocation_id=convocation.id,
            )

    def test_update_raises_when_promise_with_same_name_exists(self):
        existing_promise = ValidPromiseFactory.create()
        another_existing = ValidPromiseFactory.create()

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.service.UNIQUE_CONSTRAINT_MESSAGE.format(name=another_existing.name)),
        ):
            self.service.edit_promise(
                id=existing_promise.id,
                name=another_existing.name,
                description=existing_promise.description,
                sources=existing_promise.sources,
                date=existing_promise.date,
                party_id=existing_promise.party.id,
                convocation_id=existing_promise.convocation.id,
            )

    def test_update_raises_error_when_party_established_after_promise_date(self):
        convocation = ValidConvocationFactory.create()

        promise = ValidPromiseFactory.create(
            date=faker.date_between(start_date="-30y", end_date=convocation.political_parties.first().established_date),
            convocation=convocation,
            party=convocation.political_parties.first(),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.ESTABLISHED_DATE_LATER_THAN_PROMISE.format(name=promise.party.name)),
        ):
            self.mocked_service.edit_promise(
                id=promise.id,
                name=faker.word(),
                description=promise.description,
                sources=promise.sources,
                date=promise.date,
                party_id=convocation.political_parties.first().id,
                convocation_id=convocation.id,
            )

    def test_update_raises_error_when_party_liquidated_before_promise_date(self):
        convocation = ValidConvocationFactory.create()

        promise = ValidPromiseFactory.create(
            date=faker.date_between(start_date=convocation.political_parties.first().liquidated_date, end_date="today"),
            convocation=convocation,
            party=convocation.political_parties.first(),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.LIQIDATED_DATE_EARLIER_THAN_PROMISE.format(name=promise.party.name)),
        ):
            self.mocked_service.edit_promise(
                id=promise.id,
                name=faker.word(),
                description=promise.description,
                sources=promise.sources,
                date=promise.date,
                party_id=convocation.political_parties.first().id,
                convocation_id=convocation.id,
            )

    def test_delete_raises_error_promise_not_found(self):
        with self.assertRaisesMessage(
            NotFoundError,
            str(self.mocked_service.NOT_FOUND_MESSAGE),
        ):
            self.mocked_service.delete_promise(id=faker.uuid4())

    def test_delete_raises_error_when_user_is_not_owner_or_admin(self):
        author = VerifiedUserFactory.create()
        existing_promise = ValidPromiseFactory.create(created_by=author)

        non_author_user = VerifiedUserFactory.create()
        service = PromiseService(
            performed_by=non_author_user,
        )

        with self.assertRaises(PermissionViolationError):
            service.delete_promise(id=existing_promise.id)

    def test_delete_can_access_if_admin(self):
        author = VerifiedUserFactory.create()
        existing_promise = ValidPromiseFactory.create(created_by=author)

        admin_user = AdminUserFactory.create()
        service = PromiseService(
            performed_by=admin_user,
        )

        try:
            service.delete_promise(id=existing_promise.id)
        except PermissionViolationError:
            self.fail("delete_promise() raised PermissionViolationError unexpectedly for admin user!")

    def test_delete_raises_error_when_status_is_not_pending(self):
        existing_promise = ValidPromiseFactory.create(
            review_status=Promise.ReviewStatus.APPROVED,
            review_date=timezone.make_aware(faker.date_time_this_year()),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.CANNOT_DELETE_REVIEWED),
        ):
            self.mocked_service.delete_promise(id=existing_promise.id)

    def test_delete_raises_error_when_has_associated_results(self):
        result = ValidPromiseResultFactory.create(
            review_status=Promise.ReviewStatus.APPROVED,
            review_date=timezone.make_aware(faker.date_time_this_year()),
        )
        existing_promise = ValidPromiseFactory.create(
            results=[result],
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.CANNOT_DELETE_HAS_RESULTS),
        ):
            self.mocked_service.delete_promise(id=existing_promise.id)

    def test_evaluate_raises_error_when_promise_not_found(self):
        with self.assertRaisesMessage(
            NotFoundError,
            str(self.mocked_service.NOT_FOUND_MESSAGE),
        ):
            self.mocked_service.evaluate_promise(
                id=faker.uuid4(),
                new_status=Promise.ReviewStatus.APPROVED,
            )

    def test_evaluate_raises_error_when_promise_not_pending(self):
        existing_promise = ValidPromiseFactory.create(
            review_status=Promise.ReviewStatus.APPROVED,
            review_date=timezone.make_aware(faker.date_time_this_year()),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.CANNOT_EVALUATE_REVIEWED),
        ):
            self.mocked_service.evaluate_promise(
                id=existing_promise.id,
                new_status=Promise.ReviewStatus.REJECTED,
            )

    def test_evaluate_raises_error_when_status_is_the_same(self):
        existing_promise = ValidPromiseFactory.create(
            review_status=Promise.ReviewStatus.PENDING,
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.STATUSES_ARE_SAME.format(status=Promise.ReviewStatus.PENDING)),
        ):
            self.service.evaluate_promise(
                id=existing_promise.id,
                new_status=Promise.ReviewStatus.PENDING,
            )
