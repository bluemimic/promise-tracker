from django.test import TestCase

from promise_tracker.classifiers.models import PoliticalParty
from promise_tracker.classifiers.tests.factories import ValidPoliticalPartyFactory
from promise_tracker.common.services import BaseService
from promise_tracker.users.tests.factories import VerifiedUserFactory


class BaseServiceIntegrationTests(TestCase):
    def setUp(self):
        self.service = BaseService()
        self.user = VerifiedUserFactory()

    def test_create_base_creates_object_in_db(self):
        party = ValidPoliticalPartyFactory()

        result = self.service.create_base(party, performed_by=self.user)

        self.assertIsNotNone(result.id)
        self.assertEqual(PoliticalParty.objects.count(), 1)

        saved = PoliticalParty.objects.get(id=result.id)

        self.assertEqual(saved.name, party.name)
        self.assertEqual(saved.established_date, party.established_date)
        self.assertEqual(saved.liquidated_date, party.liquidated_date)

    def test_edit_base_updates_object_in_db(self):
        party = ValidPoliticalPartyFactory()
        self.service.create_base(party, performed_by=self.user)

        party.name = "def"

        result = self.service.edit_base(party, updated_by=self.user)

        self.assertEqual(result.id, party.id)
        self.assertEqual(PoliticalParty.objects.count(), 1)

        saved = PoliticalParty.objects.get(id=result.id)

        self.assertEqual(saved.name, "def")

    def test_delete_base_deletes_object_in_db(self):
        party = ValidPoliticalPartyFactory()
        self.service.create_base(party, performed_by=self.user)

        self.service.delete_base(party)

        self.assertEqual(PoliticalParty.objects.count(), 0)
