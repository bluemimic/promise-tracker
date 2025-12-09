from unittest.mock import MagicMock

from django.test import RequestFactory, TestCase
from faker import Faker

from promise_tracker.classifiers.selectors.political_party_selectors import (
    get_political_parties,
    get_political_party_by_id,
)
from promise_tracker.classifiers.services.political_party_services import PoliticalPartyService
from promise_tracker.classifiers.tests.factories import ValidPoliticalPartyFactory
from promise_tracker.core.exceptions import NotFoundError
from promise_tracker.users.models import BaseUser

faker = Faker()


class PoliticalPartySelectorsUnitTests(TestCase):
    def setUp(self):
        self.mock_base_service = MagicMock()

        self.mocked_service = PoliticalPartyService(
            performed_by=MagicMock(spec=BaseUser),
            base_service=self.mock_base_service,
        )

    def test_view_all_returns_none_when_no_political_parties(self):
        political_parties = get_political_parties()

        self.assertListEqual(list(political_parties), [])

    def test_view_all_returns_none_when_no_filters_match(self):
        ValidPoliticalPartyFactory.create(
            name="Party One",
        )
        ValidPoliticalPartyFactory.create(
            name="Party Two",
            established_date=faker.date_between(start_date="-20d", end_date="-15d"),
            liquidated_date=faker.date_between(start_date="-10d", end_date="-5d"),
        )

        filters = {
            "name": "Nonexistent Party",
            "is_active": "true",
        }

        political_parties = get_political_parties(filters=filters)

        self.assertListEqual(list(political_parties), [])

    def test_view_all_returns_filtered_political_parties_when_exist(self):
        party = ValidPoliticalPartyFactory.create(
            name="Party One",
            liquidated_date=None,
        )
        ValidPoliticalPartyFactory.create(
            name="Party Two",
            established_date=faker.date_between(start_date="-20d", end_date="-15d"),
            liquidated_date=faker.date_between(start_date="-10d", end_date="-5d"),
        )

        filters = {
            "name": "Party",
            "is_active": "true",
        }

        political_parties = get_political_parties(filters=filters)

        self.assertEqual(political_parties.count(), 1)
        self.assertEqual(political_parties.first().id, party.id)

    def test_view_by_id_returns_political_party_when_exists(self):
        party = ValidPoliticalPartyFactory.create()

        fetched_party = get_political_party_by_id(id=party.id)

        self.assertEqual(fetched_party.id, party.id)

    def test_view_by_id_raises_not_found_error_when_political_party_does_not_exist(self):
        non_existent_id = faker.uuid4()

        with self.assertRaisesMessage(
            NotFoundError,
            str(self.mocked_service.NOT_FOUND_MESSAGE),
        ):
            get_political_party_by_id(id=non_existent_id)
