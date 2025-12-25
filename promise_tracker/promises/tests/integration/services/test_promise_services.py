from unittest.mock import MagicMock, patch

from django.test import TestCase
from faker import Faker

from promise_tracker.promises.models import Promise
from promise_tracker.promises.services.promise_services import PromiseService
from promise_tracker.promises.tests.factories import ValidPromiseFactory
from promise_tracker.users.tests.factories import AdminUserFactory, VerifiedUserFactory

faker = Faker()


class PromiseServicesIntegrationTests(TestCase):
    def setUp(self):
        self.mock_base_service = MagicMock()
        self.performed_by = VerifiedUserFactory.create()

        self.service = PromiseService(
            performed_by=self.performed_by,
            base_service=self.mock_base_service,
        )

    def test_create_calls_base_when_promise_with_valid_data(self):
        promise = ValidPromiseFactory.create()

        self.service.create_promise(
            name=promise.name,
            description=promise.description,
            sources=promise.sources,
            date=promise.date,
            party_id=promise.party.id,
            convocation_id=promise.convocation.id,
        )

        self.mock_base_service.create_base.assert_called_once()

    def test_edit_calls_base_when_promise_with_valid_data(self):
        existing_promise = ValidPromiseFactory.create()

        self.service.performed_by = AdminUserFactory.create()

        self.service.edit_promise(
            id=existing_promise.id,
            name=faker.unique.word(),
            description=existing_promise.description,
            sources=existing_promise.sources,
            date=existing_promise.date,
            party_id=existing_promise.party.id,
            convocation_id=existing_promise.convocation.id,
        )

        self.mock_base_service.edit_base.assert_called_once()

    @patch("promise_tracker.promises.services.promise_services.get_object_or_raise")
    def test_delete_calls_base_when_promise_with_valid_data(self, mock_get_object):
        promise = ValidPromiseFactory.create()
        mock_get_object.return_value = promise
        
        self.service.performed_by = AdminUserFactory.create()

        self.service.delete_promise(id=promise.id)

        self.mock_base_service.delete_base.assert_called_once()

    @patch("promise_tracker.promises.services.promise_services.get_object_or_raise")
    def test_evaluate_calls_edit_base_when_valid(self, mock_get_object):
        promise = ValidPromiseFactory.create()
        mock_get_object.return_value = promise

        self.service.evaluate_promise(id=promise.id, new_status=Promise.ReviewStatus.APPROVED)

        self.mock_base_service.edit_base.assert_called_once()
