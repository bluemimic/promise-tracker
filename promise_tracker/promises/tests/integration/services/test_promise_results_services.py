from unittest.mock import MagicMock, patch

from django.test import TestCase

from promise_tracker.classifiers.tests.factories import ValidPoliticalPartyFactory
from promise_tracker.promises.models import Promise
from promise_tracker.promises.services.promise_result_services import PromiseResultService
from promise_tracker.promises.tests.factories import ValidPromiseFactory, ValidPromiseResultFactory
from promise_tracker.users.tests.factories import VerifiedUserFactory


class PromiseResultsServicesIntegrationTests(TestCase):
    def setUp(self):
        self.mock_base_service = MagicMock()
        self.performed_by = VerifiedUserFactory.create()

        self.service = PromiseResultService(
            performed_by=self.performed_by,
            base_service=self.mock_base_service,
        )

    def test_create_calls_base_when_promise_result_with_valid_data(self):
        promise = ValidPromiseFactory.create()

        result = ValidPromiseResultFactory.create(
            promise=promise,
        )

        self.service.create_result(
            promise_id=promise.id,
            status=result.status,
            description=result.description,
            sources=result.sources,
            date=result.date,
            is_final=result.is_final,
        )

        self.mock_base_service.create_base.assert_called_once()

    @patch("promise_tracker.promises.services.promise_result_services.get_object_or_raise")
    def test_edit_calls_base_when_promise_result_with_valid_data(self, mock_get_object):
        promise = ValidPromiseFactory.create()
        existing_result = ValidPromiseResultFactory.create(
            promise=promise,
        )
        mock_get_object.return_value = existing_result

        result = ValidPromiseResultFactory.create(
            promise=promise,
        )

        self.service.edit_result(
            id=existing_result.id,
            name=result.name,
            description=result.description,
            sources=result.sources,
            date=result.date,
            is_final=result.is_final,
            promise_id=promise.id,
            status=result.status,
        )

        self.mock_base_service.edit_base.assert_called_once()

    @patch("promise_tracker.promises.services.promise_result_services.get_object_or_raise")
    def test_delete_calls_base_when_promise_result_with_valid_data(self, mock_get_object):
        promise = ValidPromiseFactory.create()
        result = ValidPromiseResultFactory.create(
            promise=promise,
        )
        mock_get_object.return_value = result

        self.service.delete_result(id=result.id)

        self.mock_base_service.delete_base.assert_called_once()

    @patch("promise_tracker.promises.services.promise_result_services.get_object_or_raise")
    def test_evaluate_calls_edit_base_when_valid(self, mock_get_object):
        promise = ValidPromiseFactory.create()
        result = ValidPromiseResultFactory.create(
            promise=promise,
        )
        mock_get_object.return_value = result

        self.service.evaluate_result(id=result.id, new_status=Promise.ReviewStatus.APPROVED)

        self.mock_base_service.edit_base.assert_called_once()
