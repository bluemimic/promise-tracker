from unittest.mock import MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase

from promise_tracker.common.models import BaseModel
from promise_tracker.common.services import BaseService


class BaseServiceUnitTests(TestCase):
    def setUp(self):
        self.service = BaseService()
        self.user = MagicMock(spec=get_user_model())

    def test_create_base_calls_save_and_sets_audit_fields(self):
        instance = MagicMock(spec=BaseModel)

        result = self.service.create_base(instance, performed_by=self.user)

        instance.full_clean.assert_called_once()
        instance.save.assert_called_once()

        self.assertEqual(result, instance)
        self.assertEqual(instance.created_by, self.user)
        self.assertEqual(instance.updated_by, self.user)
        self.assertIsNotNone(instance.created_at)
        self.assertIsNotNone(instance.updated_at)

    def test_edit_base_calls_save_and_updates_audit_field(self):
        instance = MagicMock(spec=BaseModel)

        result = self.service.edit_base(instance, updated_by=self.user)

        instance.full_clean.assert_called_once()
        instance.save.assert_called_once()

        self.assertEqual(result, instance)
        self.assertEqual(instance.updated_by, self.user)
        self.assertIsNotNone(instance.updated_at)

    def test_delete_base_calls_delete(self):
        instance = MagicMock(spec=BaseModel)

        self.service.delete_base(instance)

        instance.delete.assert_called_once()
