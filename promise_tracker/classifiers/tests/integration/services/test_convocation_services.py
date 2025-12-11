from unittest.mock import MagicMock, patch

from django.test import TestCase
from faker import Faker

from promise_tracker.classifiers.services.convocation_services import ConvocationService
from promise_tracker.classifiers.tests.factories import ValidConvocationFactory
from promise_tracker.users.models import BaseUser

faker = Faker()


class ConvocationServicesIntegrationTests(TestCase):
    def setUp(self):
        self.mock_base_service = MagicMock()

        self.service = ConvocationService(
            performed_by=MagicMock(spec=BaseUser),
            base_service=self.mock_base_service,
        )

    def test_create_calls_base_when_convocation_with_valid_data(self):
        convocation = ValidConvocationFactory.create()

        self.service.create_convocation(
            name=convocation.name,
            start_date=convocation.start_date,
            end_date=convocation.end_date,
            party_ids=convocation.political_parties.values_list("id", flat=True),
        )

        self.mock_base_service.create_base.assert_called_once()

    @patch("promise_tracker.classifiers.services.convocation_services.get_object_or_raise")
    def test_edit_calls_base_when_convocation_with_valid_data(self, mock_get_object):
        existing_convocation = ValidConvocationFactory.create()
        mock_get_object.return_value = existing_convocation

        convocation = ValidConvocationFactory.build()

        self.service.edit_convocation(
            id=convocation.id,
            name=convocation.name,
            start_date=convocation.start_date,
            end_date=convocation.end_date,
            party_ids=existing_convocation.political_parties.values_list("id", flat=True),
        )

        self.mock_base_service.edit_base.assert_called_once()

    @patch("promise_tracker.classifiers.services.convocation_services.get_object_or_raise")
    def test_delete_calls_base_when_convocation_with_valid_data(self, mock_get_object):
        existing_convocation = ValidConvocationFactory.create()
        mock_get_object.return_value = existing_convocation

        self.service.delete_convocation(id=existing_convocation.id)

        self.mock_base_service.delete_base.assert_called_once()
