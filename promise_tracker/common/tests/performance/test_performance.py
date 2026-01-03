import time

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from faker import Faker

from promise_tracker.classifiers.models import PoliticalParty
from promise_tracker.promises.tests.factories import ValidPromiseFactory

faker = Faker()


class PromisesPerformanceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        ValidPromiseFactory.create_batch(1000)

    def test_promises_list_95th_percentile(self):
        url = reverse("promises:promises:list")

        durations = []
        runs = 50

        for _ in range(runs):
            start = time.perf_counter()
            response = self.client.get(url)
            duration = time.perf_counter() - start
            durations.append(duration)
            self.assertEqual(response.status_code, 200)

        durations.sort()
        idx = max(0, int(0.95 * len(durations)) - 1)
        p95 = durations[idx]

        max_duration = 3.0
        self.assertLess(p95, max_duration)

    def test_pagination_present_and_works(self):
        url = reverse("promises:promises:list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertIn("page_obj", response.context)
        page_obj = response.context["page_obj"]

        self.assertEqual(page_obj.paginator.per_page, settings.PAGINATE_BY_DEFAULT)
