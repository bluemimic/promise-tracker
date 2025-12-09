from unittest.mock import MagicMock, patch

from django.test import RequestFactory, TestCase
from faker import Faker

from promise_tracker.classifiers.services.political_party_services import PoliticalPartyService
from promise_tracker.classifiers.tests.factories import ValidPoliticalPartyFactory
from promise_tracker.users.models import BaseUser

faker = Faker()


class PoliticalPartyServicesIntegrationTests(TestCase):
    def setUp(self):
        self.mock_base_service = MagicMock()

        self.service = PoliticalPartyService(
            performed_by=MagicMock(spec=BaseUser),
            base_service=self.mock_base_service,
        )

    def test_create_calls_base_when_political_party_with_valid_data(self):
        party = ValidPoliticalPartyFactory.build()

        self.service.create_political_party(
            name=party.name,
            established_date=party.established_date,
            liquidated_date=party.liquidated_date,
        )

        self.mock_base_service.create_base.assert_called_once()

    @patch("promise_tracker.classifiers.services.political_party_services.get_object_or_raise")
    def test_update_calls_base_when_political_party_with_valid_data(self, mock_get_object):
        existing_party = ValidPoliticalPartyFactory.build()
        mock_get_object.return_value = existing_party

        party = ValidPoliticalPartyFactory.build()

        self.service.edit_political_party(
            id=party.id,
            name=party.name,
            established_date=party.established_date,
            liquidated_date=party.liquidated_date,
        )

        self.mock_base_service.edit_base.assert_called_once()

    @patch("promise_tracker.classifiers.services.political_party_services.get_object_or_raise")
    def test_delete_calls_base_when_political_party_with_valid_data(self, mock_get_object):
        existing_party = ValidPoliticalPartyFactory.create()
        mock_get_object.return_value = existing_party

        self.service.delete_political_party(id=existing_party.id)

        self.mock_base_service.delete_base.assert_called_once()
