from __future__ import annotations

import random

from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker

from promise_tracker.classifiers.tests.factories import (
    ValidConvocationFactory,
    ValidPoliticalPartyFactory,
)
from promise_tracker.promises.models import PromiseResult
from promise_tracker.promises.tests.factories import (
    ValidPromiseFactory,
    ValidPromiseResultFactory,
)
from promise_tracker.users.tests.factories import AdminUserFactory, VerifiedUserFactory

faker = Faker()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--users",
            type=int,
            default=10,
            help="Number of users to create (default: 10)",
        )
        parser.add_argument(
            "--parties",
            type=int,
            default=10,
            help="Number of political parties to create (default: 10)",
        )
        parser.add_argument(
            "--convocations",
            type=int,
            default=5,
            help="Number of convocations to create (default: 5)",
        )
        parser.add_argument(
            "--promises",
            type=int,
            default=20,
            help="Number of promises to create (default: 100)",
        )
        parser.add_argument(
            "--results",
            type=int,
            default=5,
            help="Number of results to create per promise (default: 30)",
        )
        parser.add_argument(
            "--ensure-final",
            action="store_true",
            help="Ensure exactly one result per promise is marked as final",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=None,
            help="Optional random seed for reproducible data",
        )

    def handle(self, *args, **options):
        users_count: int = options["users"]
        parties_count: int = options["parties"]
        convocations_count: int = options["convocations"]
        promises_count: int = options["promises"]
        results_per_promise: int = options["results"]
        ensure_final: bool = options["ensure_final"]
        seed = options.get("seed")

        if seed is not None:
            random.seed(seed)

        self.stdout.write(self.style.NOTICE("Seeding database with test data..."))

        try:
            with transaction.atomic():
                admins = AdminUserFactory.create_batch(3)

                users = VerifiedUserFactory.create_batch(users_count)

                all_users = admins + users

                parties = ValidPoliticalPartyFactory.create_batch(parties_count, created_by=random.choice(admins))

                convocations = ValidConvocationFactory.create_batch(
                    convocations_count,
                    political_parties=random.sample(parties, k=max(1, parties_count // convocations_count)),
                    created_by=random.choice(admins),
                )

                promises = []

                for _ in range(promises_count):
                    if random.random() < 0.4:
                        promise = ValidPromiseFactory.create(
                            convocation=random.choice(convocations),
                            created_by=random.choice(all_users),
                            review_status=random.choice(
                                [
                                    PromiseResult.ReviewStatus.APPROVED,
                                    PromiseResult.ReviewStatus.REJECTED,
                                ]
                            ),
                            review_date=faker.date_time_between(start_date="-1y", end_date="now"),
                            reviewer=random.choice(admins),
                        )
                    else:
                        promise = ValidPromiseFactory.create(
                            convocation=random.choice(convocations),
                            created_by=random.choice(all_users),
                        )

                    promises.append(promise)

                reviewed_promises = [p for p in promises if p.is_reviewed]

                for promise in promises:
                    results = []

                    for _ in range(results_per_promise):
                        if random.random() < 0.4:
                            result = ValidPromiseResultFactory.create(
                                promise=promise,
                                created_by=random.choice(all_users),
                                review_status=random.choice(
                                    [
                                        PromiseResult.ReviewStatus.APPROVED,
                                        PromiseResult.ReviewStatus.REJECTED,
                                    ]
                                ),
                                review_date=faker.date_time_between(start_date="-1y", end_date="now"),
                                reviewer=random.choice(admins),
                            )
                        else:
                            result = ValidPromiseResultFactory.create(
                                promise=promise,
                                created_by=random.choice(all_users),
                            )

                        results.append(result)

                    if (
                        ensure_final
                        and promise in reviewed_promises
                        and any(r.review_status == PromiseResult.ReviewStatus.APPROVED for r in results)
                    ):
                        chosen = random.choice(
                            [r for r in results if r.review_status == PromiseResult.ReviewStatus.APPROVED]
                        )

                        chosen.is_final = True
                        chosen.status = PromiseResult.CompletionStatus.COMPLETED

                        chosen.save()

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Seeding interrupted by user"))

        self.stdout.write(self.style.SUCCESS("Seeding finished successfully."))
