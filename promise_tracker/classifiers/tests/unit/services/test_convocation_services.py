import datetime
import random
from unittest.mock import MagicMock, patch

from django.test import TestCase
from faker import Faker

from promise_tracker.classifiers.services.convocation_services import ConvocationService
from promise_tracker.classifiers.tests.factories import (
    ValidConvocationFactory,
    ValidPoliticalPartyFactory,
)
from promise_tracker.core.exceptions import ApplicationError, NotFoundError
from promise_tracker.promises.tests.factories import ValidPromiseFactory
from promise_tracker.users.models import BaseUser
from promise_tracker.users.tests.factories import VerifiedUserFactory

faker = Faker()


class ConvocationServicesUnitTests(TestCase):
    def setUp(self):
        self.mock_base_service = MagicMock()

        self.mocked_service = ConvocationService(
            performed_by=MagicMock(spec=BaseUser),
            base_service=self.mock_base_service,
        )

        self.service = ConvocationService(
            performed_by=VerifiedUserFactory.create(),
        )

    def test_create_raises_error_when_start_date_is_in_future(self):
        convocation = ValidConvocationFactory.build(
            start_date=faker.date_between(start_date="+1d", end_date="+10d"),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.START_DATE_IN_FUTURE),
        ):
            self.mocked_service.create_convocation(
                name=convocation.name,
                start_date=convocation.start_date,
                end_date=convocation.end_date,
                party_ids=[],
            )

    def test_create_raises_error_when_end_date_is_in_future(self):
        convocation = ValidConvocationFactory.build(
            end_date=faker.date_between(start_date="+1d", end_date="+10d"),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.END_DATE_IN_FUTURE),
        ):
            self.mocked_service.create_convocation(
                name=convocation.name,
                start_date=convocation.start_date,
                end_date=convocation.end_date,
                party_ids=[],
            )

    def test_create_raises_error_when_end_date_smaller_than_start_date(self):
        convocation = ValidConvocationFactory.build(
            start_date=faker.date_between(start_date="-5d", end_date="-1d"),
            end_date=faker.date_between(start_date="-10d", end_date="-6d"),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.END_DATE_SMALLER_THAN_START),
        ):
            self.mocked_service.create_convocation(
                name=convocation.name,
                start_date=convocation.start_date,
                end_date=convocation.end_date,
                party_ids=[],
            )

    def test_raises_error_when_party_list_is_empty(self):
        convocation = ValidConvocationFactory.build()

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.PARTIES_LIST_EMPTY),
        ):
            self.mocked_service.create_convocation(
                name=convocation.name,
                start_date=convocation.start_date,
                end_date=convocation.end_date,
                party_ids=[],
            )

    def test_create_raises_error_when_party_in_list_does_not_exist(self):
        convocation = ValidConvocationFactory.build()

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.PARTIES_LIST_INVALID),
        ):
            self.mocked_service.create_convocation(
                name=convocation.name,
                start_date=convocation.start_date,
                end_date=convocation.end_date,
                party_ids=[faker.uuid4()],
            )

    def test_create_raises_error_when_party_liquidated_before_convocation_start_date(self):
        convocation = ValidConvocationFactory.create()
        invalid_party = ValidPoliticalPartyFactory.create(
            established_date=convocation.start_date - datetime.timedelta(days=random.randint(15, 20)),
            liquidated_date=convocation.start_date - datetime.timedelta(days=random.randint(1, 10)),
        )
        convocation.political_parties.add(invalid_party)

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.PARTY_LIQUIDATED_BEFORE_START.format(party_name=invalid_party.name)),
        ):
            self.mocked_service.create_convocation(
                name=convocation.name,
                start_date=convocation.start_date,
                end_date=convocation.end_date,
                party_ids=[invalid_party.id],
            )

    def test_create_raises_error_when_party_established_before_convocation_end_date(self):
        convocation = ValidConvocationFactory.create()
        invalid_party = ValidPoliticalPartyFactory.create(
            established_date=convocation.end_date + datetime.timedelta(days=random.randint(1, 10)),
            liquidated_date=convocation.end_date + datetime.timedelta(days=random.randint(15, 20)),
        )
        convocation.political_parties.add(invalid_party)

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.PARTY_ESTABLISHED_AFTER_END.format(party_name=invalid_party.name)),
        ):
            self.mocked_service.create_convocation(
                name=convocation.name,
                start_date=convocation.start_date,
                end_date=convocation.end_date,
                party_ids=[invalid_party.id],
            )

    def test_create_raises_error_when_convocation_exists(self):
        convocation = ValidConvocationFactory.create()

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.service.UNIQUE_CONSTRAINT_MESSAGE.format(name=convocation.name)),
        ):
            self.service.create_convocation(
                name=convocation.name,
                start_date=convocation.start_date,
                end_date=convocation.end_date,
                party_ids=list(convocation.political_parties.all().values_list("id", flat=True)),
            )

    @patch("promise_tracker.classifiers.services.convocation_services.get_object_or_raise")
    def test_edit_raises_error_when_start_date_is_in_future(self, mock_get_object):
        existing_convocation = ValidConvocationFactory.build()
        mock_get_object.return_value = existing_convocation

        convocation = ValidConvocationFactory.build(
            start_date=faker.date_between(start_date="+1d", end_date="+10d"),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.START_DATE_IN_FUTURE),
        ):
            self.mocked_service.edit_convocation(
                id=existing_convocation.id,
                name=convocation.name,
                start_date=convocation.start_date,
                end_date=convocation.end_date,
                party_ids=[],
            )

    @patch("promise_tracker.classifiers.services.convocation_services.get_object_or_raise")
    def test_edit_raises_error_when_end_date_is_in_future(self, mock_get_object):
        existing_convocation = ValidConvocationFactory.build()
        mock_get_object.return_value = existing_convocation

        convocation = ValidConvocationFactory.build(
            end_date=faker.date_between(start_date="+1d", end_date="+10d"),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.END_DATE_IN_FUTURE),
        ):
            self.mocked_service.edit_convocation(
                id=existing_convocation.id,
                name=convocation.name,
                start_date=convocation.start_date,
                end_date=convocation.end_date,
                party_ids=[],
            )

    @patch("promise_tracker.classifiers.services.convocation_services.get_object_or_raise")
    def test_edit_raises_error_when_end_date_smaller_than_start_date(self, mock_get_object):
        existing_convocation = ValidConvocationFactory.build()
        mock_get_object.return_value = existing_convocation

        convocation = ValidConvocationFactory.build(
            start_date=faker.date_between(start_date="-5d", end_date="-1d"),
            end_date=faker.date_between(start_date="-10d", end_date="-6d"),
        )

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.END_DATE_SMALLER_THAN_START),
        ):
            self.mocked_service.edit_convocation(
                id=existing_convocation.id,
                name=convocation.name,
                start_date=convocation.start_date,
                end_date=convocation.end_date,
                party_ids=[],
            )

    @patch("promise_tracker.classifiers.services.convocation_services.get_object_or_raise")
    def test_edit_raises_error_when_party_list_is_empty(self, mock_get_object):
        existing_convocation = ValidConvocationFactory.build()
        mock_get_object.return_value = existing_convocation

        convocation = ValidConvocationFactory.build()

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.PARTIES_LIST_EMPTY),
        ):
            self.mocked_service.edit_convocation(
                id=existing_convocation.id,
                name=convocation.name,
                start_date=convocation.start_date,
                end_date=convocation.end_date,
                party_ids=None,
            )

    @patch("promise_tracker.classifiers.services.convocation_services.get_object_or_raise")
    def test_edit_raises_error_when_party_in_list_does_not_exist(self, mock_get_object):
        existing_convocation = ValidConvocationFactory.build()
        mock_get_object.return_value = existing_convocation

        convocation = ValidConvocationFactory.build()

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.PARTIES_LIST_INVALID),
        ):
            self.mocked_service.edit_convocation(
                id=existing_convocation.id,
                name=convocation.name,
                start_date=convocation.start_date,
                end_date=convocation.end_date,
                party_ids=[faker.uuid4()],
            )

    @patch("promise_tracker.classifiers.services.convocation_services.get_object_or_raise")
    def test_edit_raises_error_when_party_liquidated_before_convocation_start_date(self, mock_get_object):
        existing_convocation = ValidConvocationFactory.build()
        mock_get_object.return_value = existing_convocation

        convocation = ValidConvocationFactory.create()
        party = ValidPoliticalPartyFactory.create(
            established_date=convocation.start_date - datetime.timedelta(days=random.randint(15, 20)),
            liquidated_date=convocation.start_date - datetime.timedelta(days=random.randint(1, 10)),
        )
        convocation.political_parties.add(party)

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.PARTY_LIQUIDATED_BEFORE_START.format(party_name=party.name)),
        ):
            self.mocked_service.edit_convocation(
                id=existing_convocation.id,
                name=convocation.name,
                start_date=convocation.start_date,
                end_date=convocation.end_date,
                party_ids=[party.id],
            )

    @patch("promise_tracker.classifiers.services.convocation_services.get_object_or_raise")
    def test_edit_raises_error_when_party_established_before_convocation_end_date(self, mock_get_object):
        existing_convocation = ValidConvocationFactory.build()
        mock_get_object.return_value = existing_convocation

        convocation = ValidConvocationFactory.create()
        party = ValidPoliticalPartyFactory.create(
            established_date=convocation.end_date + datetime.timedelta(days=random.randint(1, 10)),
            liquidated_date=convocation.end_date + datetime.timedelta(days=random.randint(15, 20)),
        )
        convocation.political_parties.add(party)

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.PARTY_ESTABLISHED_AFTER_END.format(party_name=party.name)),
        ):
            self.mocked_service.edit_convocation(
                id=existing_convocation.id,
                name=convocation.name,
                start_date=convocation.start_date,
                end_date=convocation.end_date,
                party_ids=[party.id],
            )

    def test_edit_raises_error_when_convocation_does_not_exist(self):
        convocation = ValidConvocationFactory.build()
        non_existent_id = faker.uuid4()

        with self.assertRaisesMessage(
            NotFoundError,
            str(self.mocked_service.NOT_FOUND_MESSAGE),
        ):
            self.mocked_service.edit_convocation(
                id=non_existent_id,
                name=convocation.name,
                start_date=convocation.start_date,
                end_date=convocation.end_date,
                party_ids=[],
            )

    @patch("promise_tracker.classifiers.services.convocation_services.get_object_or_raise")
    def test_edit_raises_error_when_convocation_exists(self, mock_get_object):
        convocations = ValidConvocationFactory.create_batch(2)

        convocation_to_change = convocations[0]
        existing_convocation_name = convocations[1].name

        mock_get_object.return_value = convocation_to_change

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.service.UNIQUE_CONSTRAINT_MESSAGE.format(name=existing_convocation_name)),
        ):
            self.service.edit_convocation(
                id=convocation_to_change.id,
                name=existing_convocation_name,
                start_date=convocation_to_change.start_date,
                end_date=convocation_to_change.end_date,
                party_ids=list(convocation_to_change.political_parties.all().values_list("id", flat=True)),
            )

    def test_delete_raises_error_when_convocation_does_not_exist(self):
        non_existent_id = faker.uuid4()

        with self.assertRaisesMessage(
            NotFoundError,
            str(self.mocked_service.NOT_FOUND_MESSAGE),
        ):
            self.mocked_service.delete_convocation(id=non_existent_id)

    @patch("promise_tracker.classifiers.services.convocation_services.get_object_or_raise")
    def test_delete_raises_error_when_has_associated_promises(self, mock_get_object):
        convocation = ValidConvocationFactory.create()
        ValidPromiseFactory.create_batch(2, convocation=convocation)

        mock_get_object.return_value = convocation

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.mocked_service.CANNOT_DELETE_HAS_ASSOCIATED_PROMISES),
        ):
            self.mocked_service.delete_convocation(id=convocation.id)
