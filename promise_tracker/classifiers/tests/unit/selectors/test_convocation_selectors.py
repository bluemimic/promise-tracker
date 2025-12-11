from unittest.mock import MagicMock

from django.test import TestCase
from faker import Faker

from promise_tracker.classifiers.selectors.convocation_selectors import (
    get_convocation_by_id,
    get_convocations,
)
from promise_tracker.classifiers.services.convocation_services import ConvocationService
from promise_tracker.classifiers.tests.factories import ValidConvocationFactory, ValidPoliticalPartyFactory
from promise_tracker.core.exceptions import NotFoundError
from promise_tracker.users.models import BaseUser

faker = Faker()


class ConvocationSelectorsUnitTests(TestCase):
    def setUp(self):
        self.mock_base_service = MagicMock()

        self.mocked_service = ConvocationService(
            performed_by=MagicMock(spec=BaseUser),
            base_service=self.mock_base_service,
        )

    def test_view_all_returns_none_when_no_convocations(self):
        convocations = get_convocations()

        self.assertListEqual(list(convocations), [])

    def test_view_all_returns_none_when_no_filters_match(self):
        ValidConvocationFactory.create(
            name="1",
        )
        ValidConvocationFactory.create(
            name="2",
        )

        party = ValidPoliticalPartyFactory.create()

        filters = {
            "name": "3",
            "political_parties": [party.id],
        }

        convocations = get_convocations(filters=filters)

        self.assertListEqual(list(convocations), [])

    def test_view_all_returns_filtered_convocations_when_exist(self):
        convocation = ValidConvocationFactory.create(
            name="Convocation One",
        )
        ValidConvocationFactory.create(
            name="Convocation Two",
        )

        filters = {
            "name": "Convocation",
            "political_parties": convocation.political_parties.values_list("id", flat=True),
        }

        convocations = get_convocations(filters=filters)

        self.assertEqual(convocations.count(), 1)
        self.assertEqual(convocations.first().id, convocation.id)

    def test_view_by_id_returns_convocation_when_exists(self):
        convocation = ValidConvocationFactory.create()

        fetched_convocation = get_convocation_by_id(id=convocation.id)

        self.assertEqual(fetched_convocation.id, convocation.id)

    def test_view_by_id_raises_not_found_error_when_convocation_does_not_exist(self):
        non_existent_id = faker.uuid4()

        with self.assertRaisesMessage(
            NotFoundError,
            str(self.mocked_service.NOT_FOUND_MESSAGE),
        ):
            get_convocation_by_id(id=non_existent_id)
