from unittest.mock import MagicMock, patch

from django.test import RequestFactory, TestCase
from faker import Faker

from promise_tracker.classifiers.services.political_party_services import PoliticalPartyService
from promise_tracker.classifiers.tests.factories import ValidConvocationFactory, ValidPoliticalPartyFactory
from promise_tracker.core.exceptions import ApplicationError, NotFoundError
from promise_tracker.promises.tests.factories import ValidPromiseFactory
from promise_tracker.users.models import BaseUser
from promise_tracker.users.tests.factories import VerifiedUserFactory

faker = Faker()


class PoliticalPartyServicesUnitTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.mock_base_service = MagicMock()

        self.mocked_service = PoliticalPartyService(
            performed_by=MagicMock(spec=BaseUser),
            base_service=self.mock_base_service,
        )

        self.service = PoliticalPartyService(
            performed_by=VerifiedUserFactory.create(),
        )

    def test_create_raises_error_when_established_date_in_future(self):
        party = ValidPoliticalPartyFactory.build(established_date=faker.date_between(start_date="+1d", end_date="+10d"))

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.ESTABLISHED_DATE_IN_FUTURE),
        ):
            self.mocked_service.create_political_party(
                name=party.name,
                established_date=party.established_date,
            )

    def test_create_raises_error_when_liquidated_date_in_future(self):
        party = ValidPoliticalPartyFactory.build(
            liquidated_date=faker.date_between(start_date="+1d", end_date="+10d"),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.LIQUIDATED_DATE_IN_FUTURE),
        ):
            self.mocked_service.create_political_party(
                name=party.name,
                established_date=party.established_date,
                liquidated_date=party.liquidated_date,
            )

    def test_create_raises_error_when_liquidated_date_smaller_than_established_date(self):
        party = ValidPoliticalPartyFactory.build(
            established_date=faker.date_between(start_date="-10d", end_date="-5d"),
            liquidated_date=faker.date_between(start_date="-20d", end_date="-15d"),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.LIQUIDATED_DATE_SMALLER_THAN_ESTABLISHED_DATE),
        ):
            self.mocked_service.create_political_party(
                name=party.name,
                established_date=party.established_date,
                liquidated_date=party.liquidated_date,
            )

    def test_create_raises_error_when_political_party_exists(self):
        party = ValidPoliticalPartyFactory.create()

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.service.UNIQUE_CONSTRAINT_MESSAGE.format(name=party.name)),
        ):
            self.service.create_political_party(
                name=party.name,
                established_date=party.established_date,
                liquidated_date=party.liquidated_date,
            )

    @patch("promise_tracker.classifiers.services.political_party_services.get_object_or_raise")
    def test_update_raises_error_when_established_date_in_future(self, mock_get_object):
        existing_party = ValidPoliticalPartyFactory.build()
        mock_get_object.return_value = existing_party

        party = ValidPoliticalPartyFactory.build(
            established_date=faker.date_between(start_date="+1d", end_date="+10d"),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.ESTABLISHED_DATE_IN_FUTURE),
        ):
            self.mocked_service.edit_political_party(
                id=party.id,
                name=party.name,
                established_date=party.established_date,
                liquidated_date=party.liquidated_date,
            )

    @patch("promise_tracker.classifiers.services.political_party_services.get_object_or_raise")
    def test_update_raises_error_when_liquidated_date_in_future(self, mock_get_object):
        existing_party = ValidPoliticalPartyFactory.build()
        mock_get_object.return_value = existing_party

        party = ValidPoliticalPartyFactory.build(
            liquidated_date=faker.date_between(start_date="+1d", end_date="+10d"),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.LIQUIDATED_DATE_IN_FUTURE),
        ):
            self.mocked_service.edit_political_party(
                id=party.id,
                name=party.name,
                established_date=party.established_date,
                liquidated_date=party.liquidated_date,
            )

    @patch("promise_tracker.classifiers.services.political_party_services.get_object_or_raise")
    def test_update_raises_error_when_liquidated_date_smaller_than_established_date_raises_application_error(
        self, mock_get_object
    ):
        existing_party = ValidPoliticalPartyFactory.build()
        mock_get_object.return_value = existing_party

        party = ValidPoliticalPartyFactory.build(
            established_date=faker.date_between(start_date="-10d", end_date="-5d"),
            liquidated_date=faker.date_between(start_date="-20d", end_date="-15d"),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.LIQUIDATED_DATE_SMALLER_THAN_ESTABLISHED_DATE),
        ):
            self.mocked_service.edit_political_party(
                id=party.id,
                name=party.name,
                established_date=party.established_date,
                liquidated_date=party.liquidated_date,
            )

    def test_update_raises_error_when_political_party_does_not_exist(self):
        party = ValidPoliticalPartyFactory.build()
        non_existent_id = faker.uuid4()

        with self.assertRaisesMessage(
            NotFoundError,
            str(self.mocked_service.NOT_FOUND_MESSAGE),
        ):
            self.mocked_service.edit_political_party(
                id=non_existent_id,
                name=party.name,
                established_date=party.established_date,
                liquidated_date=party.liquidated_date,
            )

    @patch("promise_tracker.classifiers.services.political_party_services.get_object_or_raise")
    def test_update_raises_error_when_political_party_exists(self, mock_get_object):
        parties = ValidPoliticalPartyFactory.create_batch(2)

        party_to_change = parties[0]
        existing_party_name = parties[1].name

        mock_get_object.return_value = party_to_change

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.service.UNIQUE_CONSTRAINT_MESSAGE.format(name=existing_party_name)),
        ):
            self.service.edit_political_party(
                id=party_to_change.id,
                name=existing_party_name,
                established_date=party_to_change.established_date,
                liquidated_date=party_to_change.liquidated_date,
            )

    def test_delete_raises_error_when_political_party_does_not_exist(self):
        non_existent_id = faker.uuid4()

        with self.assertRaisesMessage(
            NotFoundError,
            str(self.mocked_service.NOT_FOUND_MESSAGE),
        ):
            self.mocked_service.delete_political_party(id=non_existent_id)

    @patch("promise_tracker.classifiers.services.political_party_services.get_object_or_raise")
    def test_delete_raises_error_when_elected_in_convocation(self, mock_get_object):
        party = ValidPoliticalPartyFactory.create()
        ValidConvocationFactory.create(political_parties=[party])

        mock_get_object.return_value = party

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.CANNOT_DELETE_ELECTED_IN_CONVOCATIONS),
        ):
            self.mocked_service.delete_political_party(id=party.id)

    @patch("promise_tracker.classifiers.services.political_party_services.get_object_or_raise")
    def test_delete_raises_error_when_has_associated_promises(self, mock_get_object):
        party = ValidPoliticalPartyFactory.create()
        ValidPromiseFactory.create(party=party)

        mock_get_object.return_value = party

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.CANNOT_DELETE_HAS_ASSOCIATED_PROMISES),
        ):
            self.mocked_service.delete_political_party(id=party.id)
