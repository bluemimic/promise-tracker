from django.test import TestCase
from faker import Faker

from promise_tracker.users.tests.factories import UniversalUnverifiedUserFactory


class BaseUserTests(TestCase):
    def test_set_verification_code(self):
        user = UniversalUnverifiedUserFactory(is_verified=False)

        user.set_verification_code(Faker().text(max_nb_chars=255), Faker().future_datetime())

        self.assertIsNotNone(user.verification_code)
        self.assertIsNotNone(user.verification_code_expires_at)
