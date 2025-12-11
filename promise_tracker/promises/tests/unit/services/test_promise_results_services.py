from datetime import timedelta
from unittest.mock import MagicMock

from django.test import RequestFactory, TestCase
from django.utils import timezone
from faker import Faker

from promise_tracker.core.exceptions import ApplicationError, NotFoundError, PermissionViolationError
from promise_tracker.promises.models import PromiseResult
from promise_tracker.promises.services.promise_result_services import PromiseResultService
from promise_tracker.promises.tests.factories import ValidPromiseFactory, ValidPromiseResultFactory
from promise_tracker.users.models import BaseUser
from promise_tracker.users.tests.factories import AdminUserFactory, VerifiedUserFactory

faker = Faker()


class PromiseResultServicesUnitTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.mock_base_service = MagicMock()

        self.mocked_service = PromiseResultService(
            performed_by=MagicMock(spec=BaseUser),
            base_service=self.mock_base_service,
        )

        self.service = PromiseResultService(
            performed_by=AdminUserFactory.create(),
        )

    def test_create_raises_error_when_result_date_in_future(self):
        promise = ValidPromiseFactory.create()

        result = ValidPromiseResultFactory.create(
            promise=promise,
            date=timezone.now().date() + timedelta(days=1),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.DATE_IN_FUTURE),
        ):
            self.mocked_service.create_result(
                name=faker.word(),
                description=result.description,
                sources=result.sources,
                is_final=result.is_final,
                date=result.date,
                promise_id=promise.id,
            )

    def test_create_raises_error_when_promise_not_found(self):
        promise_result = ValidPromiseResultFactory.create()

        with self.assertRaisesMessage(
            NotFoundError,
            str(self.mocked_service.PROMISE_NOT_FOUND),
        ):
            self.mocked_service.create_result(
                name=faker.word(),
                description=promise_result.description,
                sources=promise_result.sources,
                is_final=promise_result.is_final,
                date=promise_result.date,
                promise_id=faker.uuid4(),
            )

    def test_create_raises_error_when_approved_final_exists(self):
        promise = ValidPromiseFactory.create()
        ValidPromiseResultFactory.create(
            promise=promise,
            is_final=True,
            status=PromiseResult.CompletionStatus.COMPLETED,
            review_status=PromiseResult.ReviewStatus.APPROVED,
            review_date=timezone.now(),
            date=promise.date,
        )

        result_to_add = ValidPromiseResultFactory.create()

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.CANNOT_ADD_TO_FINAL_PROMISE),
        ):
            self.mocked_service.create_result(
                name=faker.word(),
                description=result_to_add.description,
                sources=result_to_add.sources,
                is_final=result_to_add.is_final,
                date=result_to_add.date,
                promise_id=promise.id,
            )

    def test_create_raises_error_when_later_final_exists(self):
        promise = ValidPromiseFactory.create()

        later = ValidPromiseResultFactory.create(
            promise=promise,
            review_status=PromiseResult.ReviewStatus.APPROVED,
            review_date=timezone.now(),
            date=promise.date + timedelta(days=10),
        )

        result_to_add = ValidPromiseResultFactory.create(
            is_final=True,
            status=PromiseResult.CompletionStatus.COMPLETED,
            date=promise.date + timedelta(days=1),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.CANNOT_ADD_FINAL_BECAUSE_LATER_RESULTS),
        ):
            self.mocked_service.create_result(
                name=faker.word(),
                description=result_to_add.description,
                sources=result_to_add.sources,
                status=result_to_add.status,
                is_final=result_to_add.is_final,
                date=result_to_add.date,
                promise_id=promise.id,
            )

    def test_create_raises_error_when_final_status_not_specified(self):
        promise = ValidPromiseFactory.create()

        result_to_add = ValidPromiseResultFactory.create(
            is_final=True,
            status=PromiseResult.CompletionStatus.COMPLETED,
            date=promise.date + timedelta(days=1),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.FINAL_STATUS_NOT_SPECIFIED),
        ):
            self.mocked_service.create_result(
                name=faker.word(),
                description=result_to_add.description,
                sources=result_to_add.sources,
                is_final=result_to_add.is_final,
                date=result_to_add.date,
                promise_id=promise.id,
            )

    def test_create_raises_error_when_status_provided_for_non_final(self):
        promise = ValidPromiseFactory.create()

        result_to_add = ValidPromiseResultFactory.create(
            is_final=False,
            date=faker.date_between(start_date=promise.date, end_date="today"),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.STATUS_NOT_ALLOWED_FOR_NON_FINAL),
        ):
            self.mocked_service.create_result(
                name=faker.word(),
                description=result_to_add.description,
                sources=result_to_add.sources,
                is_final=result_to_add.is_final,
                date=result_to_add.date,
                promise_id=promise.id,
                status=PromiseResult.CompletionStatus.COMPLETED,
            )

    def test_create_raises_error_when_result_exists(self):
        promise = ValidPromiseFactory.create()
        existing = ValidPromiseResultFactory.create(promise=promise)

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.service.UNIQUE_CONSTRAINT_MESSAGE.format(name=existing.name)),
        ):
            self.service.create_result(
                name=existing.name,
                description=existing.description,
                sources=existing.sources,
                is_final=existing.is_final,
                date=existing.date,
                promise_id=promise.id,
                status=existing.status,
            )

    def test_create_raises_error_when_result_earlier_than_promise(self):
        promise = ValidPromiseFactory.create()

        result_to_add = ValidPromiseResultFactory.create()

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.RESULT_EARLIER_THAN_PROMISE),
        ):
            self.mocked_service.create_result(
                name=faker.word(),
                description=result_to_add.description,
                sources=result_to_add.sources,
                is_final=result_to_add.is_final,
                date=promise.date - timedelta(days=1),
                promise_id=promise.id,
            )

    def test_update_raises_error_when_result_not_found(self):
        promise = ValidPromiseFactory.create()

        result_to_update = ValidPromiseResultFactory.create()

        with self.assertRaisesMessage(
            NotFoundError,
            str(self.mocked_service.NOT_FOUND_MESSAGE),
        ):
            self.mocked_service.edit_result(
                id=faker.uuid4(),
                name=result_to_update.name,
                description=result_to_update.description,
                sources=result_to_update.sources,
                is_final=result_to_update.is_final,
                date=result_to_update.date,
                promise_id=promise.id,
                status=result_to_update.status,
            )

    def test_update_raises_error_when_user_is_not_owner_or_admin(self):
        author = VerifiedUserFactory.create()

        existing_result = ValidPromiseResultFactory.create(created_by=author)

        non_author_user = VerifiedUserFactory.create()
        service = PromiseResultService(
            performed_by=non_author_user,
        )

        with self.assertRaises(PermissionViolationError):
            service.edit_result(
                id=existing_result.id,
                name=existing_result.name,
                description=existing_result.description,
                sources=existing_result.sources,
                is_final=existing_result.is_final,
                date=existing_result.date,
                promise_id=existing_result.promise.id,
                status=existing_result.status,
            )

    def test_update_raises_error_when_reviewed(self):
        result = ValidPromiseResultFactory.create(
            review_status=PromiseResult.ReviewStatus.APPROVED,
            review_date=timezone.make_aware(faker.date_time_this_year()),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.CANNOT_EDIT_REVIEWED),
        ):
            self.mocked_service.edit_result(
                id=result.id,
                name=faker.word(),
                description=result.description,
                sources=result.sources,
                is_final=result.is_final,
                date=result.date,
                promise_id=result.promise.id,
                status=result.status,
            )

    def test_update_raises_error_when_result_date_in_future(self):
        existing_result = ValidPromiseResultFactory.create()

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.DATE_IN_FUTURE),
        ):
            self.mocked_service.edit_result(
                id=existing_result.id,
                name=faker.word(),
                description=existing_result.description,
                sources=existing_result.sources,
                is_final=existing_result.is_final,
                date=timezone.now().date() + timedelta(days=1),
                promise_id=existing_result.promise.id,
                status=existing_result.status,
            )

    def test_update_raises_error_when_promise_not_found(self):
        existing_result = ValidPromiseResultFactory.create()

        with self.assertRaisesMessage(
            NotFoundError,
            str(self.mocked_service.PROMISE_NOT_FOUND),
        ):
            self.mocked_service.edit_result(
                id=existing_result.id,
                name=faker.word(),
                description=existing_result.description,
                sources=existing_result.sources,
                is_final=existing_result.is_final,
                date=existing_result.date,
                promise_id=faker.uuid4(),
                status=existing_result.status,
            )

    def test_update_raises_error_when_has_approved_final(self):
        promise = ValidPromiseFactory.create()
        ValidPromiseResultFactory.create(
            promise=promise,
            is_final=True,
            status=PromiseResult.CompletionStatus.COMPLETED,
            review_status=PromiseResult.ReviewStatus.APPROVED,
            review_date=timezone.now(),
            date=promise.date,
        )

        existing_result = ValidPromiseResultFactory.create(promise=promise)

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.CANNOT_ADD_TO_FINAL_PROMISE),
        ):
            self.mocked_service.edit_result(
                id=existing_result.id,
                name=faker.word(),
                description=existing_result.description,
                sources=existing_result.sources,
                is_final=existing_result.is_final,
                date=existing_result.date,
                promise_id=promise.id,
                status=existing_result.status,
            )

    def test_update_raises_error_when_approved_final_exists(self):
        promise = ValidPromiseFactory.create()
        ValidPromiseResultFactory.create(
            promise=promise,
            is_final=True,
            status=PromiseResult.CompletionStatus.COMPLETED,
            review_status=PromiseResult.ReviewStatus.APPROVED,
            review_date=timezone.now(),
            date=promise.date,
        )

        result_to_update = ValidPromiseResultFactory.create(promise=promise)

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.CANNOT_ADD_TO_FINAL_PROMISE),
        ):
            self.mocked_service.edit_result(
                id=result_to_update.id,
                name=faker.word(),
                description=result_to_update.description,
                sources=result_to_update.sources,
                is_final=result_to_update.is_final,
                date=result_to_update.date,
                promise_id=promise.id,
            )

    def test_update_raises_error_when_later_final_exists(self):
        promise = ValidPromiseFactory.create()

        later = ValidPromiseResultFactory.create(
            promise=promise,
            review_status=PromiseResult.ReviewStatus.APPROVED,
            review_date=timezone.now(),
            date=promise.date + timedelta(days=10),
        )

        result_to_update = ValidPromiseResultFactory.create(
            promise=promise,
            is_final=True,
            status=PromiseResult.CompletionStatus.COMPLETED,
            date=promise.date + timedelta(days=1),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.CANNOT_ADD_FINAL_BECAUSE_LATER_RESULTS),
        ):
            self.mocked_service.edit_result(
                id=result_to_update.id,
                name=faker.word(),
                description=result_to_update.description,
                sources=result_to_update.sources,
                is_final=result_to_update.is_final,
                status=result_to_update.status,
                date=result_to_update.date,
                promise_id=promise.id,
            )

    def test_update_raises_error_when_final_status_not_specified(self):
        promise = ValidPromiseFactory.create()

        result_to_update = ValidPromiseResultFactory.create(
            promise=promise,
            is_final=True,
            status=PromiseResult.CompletionStatus.COMPLETED,
            date=promise.date + timedelta(days=1),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.FINAL_STATUS_NOT_SPECIFIED),
        ):
            self.mocked_service.edit_result(
                id=result_to_update.id,
                name=faker.word(),
                description=result_to_update.description,
                sources=result_to_update.sources,
                is_final=result_to_update.is_final,
                date=result_to_update.date,
                promise_id=promise.id,
            )

    def test_update_raises_error_when_status_provided_for_non_final(self):
        promise = ValidPromiseFactory.create()

        result_to_update = ValidPromiseResultFactory.create(
            promise=promise,
            is_final=False,
            date=faker.date_between(start_date=promise.date, end_date="today"),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.STATUS_NOT_ALLOWED_FOR_NON_FINAL),
        ):
            self.mocked_service.edit_result(
                id=result_to_update.id,
                name=faker.word(),
                description=result_to_update.description,
                sources=result_to_update.sources,
                is_final=result_to_update.is_final,
                date=result_to_update.date,
                promise_id=promise.id,
                status=PromiseResult.CompletionStatus.COMPLETED,
            )

    def test_update_raises_error_when_result_earlier_than_promise(self):
        promise = ValidPromiseFactory.create()

        result_to_update = ValidPromiseResultFactory.create(promise=promise)

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.RESULT_EARLIER_THAN_PROMISE),
        ):
            self.mocked_service.edit_result(
                id=result_to_update.id,
                name=faker.word(),
                description=result_to_update.description,
                sources=result_to_update.sources,
                is_final=result_to_update.is_final,
                date=promise.date - timedelta(days=1),
                promise_id=promise.id,
            )
        with self.assertRaisesMessage(
            NotFoundError,
            str(self.mocked_service.NOT_FOUND_MESSAGE),
        ):
            self.mocked_service.delete_result(id=faker.uuid4())

    def test_delete_raises_error_when_result_not_found(self):
        with self.assertRaisesMessage(
            NotFoundError,
            str(self.mocked_service.NOT_FOUND_MESSAGE),
        ):
            self.mocked_service.delete_result(id=faker.uuid4())

    def test_delete_raises_error_when_user_is_not_owner_or_admin(self):
        author = VerifiedUserFactory.create()
        existing_result = ValidPromiseResultFactory.create(created_by=author)

        non_author_user = VerifiedUserFactory.create()
        service = PromiseResultService(
            performed_by=non_author_user,
        )

        with self.assertRaises(PermissionViolationError):
            service.delete_result(id=existing_result.id)

    def test_delete_can_access_if_admin(self):
        admin_user = AdminUserFactory.create()
        existing_result = ValidPromiseResultFactory.create()

        service = PromiseResultService(
            performed_by=admin_user,
        )

        try:
            service.delete_result(id=existing_result.id)
        except PermissionViolationError:
            self.fail("delete_result() raised PermissionViolationError unexpectedly for admin user!")

    def test_delete_raises_error_when_status_is_not_pending(self):
        existing_result = ValidPromiseResultFactory.create(
            review_status=PromiseResult.ReviewStatus.APPROVED,
            review_date=timezone.make_aware(faker.date_time_this_year()),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.CANNOT_DELETE_REVIEWED),
        ):
            self.mocked_service.delete_result(id=existing_result.id)

    def test_evaluate_raises_error_when_result_not_found(self):
        with self.assertRaisesMessage(
            NotFoundError,
            str(self.mocked_service.NOT_FOUND_MESSAGE),
        ):
            self.mocked_service.evaluate_result(
                id=faker.uuid4(),
                new_status=PromiseResult.ReviewStatus.APPROVED,
            )

    def test_evaluate_raises_error_when_result_not_pending(self):
        existing_result = ValidPromiseResultFactory.create(
            review_status=PromiseResult.ReviewStatus.APPROVED,
            review_date=timezone.make_aware(faker.date_time_this_year()),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.CANNOT_CHANGE_STATUS),
        ):
            self.mocked_service.evaluate_result(
                id=existing_result.id,
                new_status=PromiseResult.ReviewStatus.REJECTED,
            )

    def test_evaluate_raises_when_promise_has_approved_final(self):
        promise = ValidPromiseFactory.create()
        ValidPromiseResultFactory.create(
            promise=promise,
            is_final=True,
            status=PromiseResult.CompletionStatus.COMPLETED,
            review_status=PromiseResult.ReviewStatus.APPROVED,
            review_date=timezone.now(),
            date=promise.date,
        )

        result = ValidPromiseResultFactory.create(promise=promise, review_status=PromiseResult.ReviewStatus.PENDING)

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.CANNOT_EVALUATE_BECAUSE_PROMISE_HAS_FINAL),
        ):
            self.service.evaluate_result(id=result.id, new_status=PromiseResult.ReviewStatus.APPROVED)

    def test_evaluate_raises_when_final_and_later_approved_exists(self):
        promise = ValidPromiseFactory.create()

        later = ValidPromiseResultFactory.create(
            promise=promise,
            review_status=PromiseResult.ReviewStatus.APPROVED,
            review_date=timezone.now(),
            date=promise.date + timedelta(days=10),
        )

        result = ValidPromiseResultFactory.create(
            promise=promise,
            is_final=True,
            status=PromiseResult.CompletionStatus.COMPLETED,
            review_status=PromiseResult.ReviewStatus.PENDING,
            date=promise.date + timedelta(days=1),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.CANNOT_EVALUATE_FINAL_BECAUSE_LATER_RESULTS),
        ):
            self.service.evaluate_result(id=result.id, new_status=PromiseResult.ReviewStatus.APPROVED)

    def test_evaluate_can_approve_pending_result(self):
        result = ValidPromiseResultFactory.create(review_status=PromiseResult.ReviewStatus.PENDING)

        try:
            self.service.evaluate_result(id=result.id, new_status=PromiseResult.ReviewStatus.APPROVED)
        except ApplicationError:
            self.fail("evaluate_result() raised ApplicationError unexpectedly for admin user!")
