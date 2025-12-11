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
        self.assertEqual(saved.created_by, self.user)
        self.assertEqual(saved.updated_by, self.user)
        self.assertIsNotNone(saved.created_at)
        self.assertIsNotNone(saved.updated_at)

    def test_edit_base_updates_object_in_db(self):
        party = ValidPoliticalPartyFactory()
        model = self.service.create_base(party, performed_by=self.user)
        updated_at = model.updated_at

        party.name = "def"

        another_user = VerifiedUserFactory.create()

        result = self.service.edit_base(party, updated_by=another_user)

        self.assertEqual(result.id, party.id)
        self.assertEqual(PoliticalParty.objects.count(), 1)

        saved = PoliticalParty.objects.get(id=result.id)

        self.assertEqual(saved.name, "def")
        self.assertEqual(saved.created_by, self.user)
        self.assertEqual(saved.updated_by, another_user)
        self.assertEqual(saved.created_at, model.created_at)
        self.assertNotEqual(saved.updated_at, updated_at)

    def test_delete_base_deletes_object_in_db(self):
        party = ValidPoliticalPartyFactory()
        self.service.create_base(party, performed_by=self.user)

        self.service.delete_base(party)

        self.assertEqual(PoliticalParty.objects.count(), 0)
