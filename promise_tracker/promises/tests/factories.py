from datetime import date
from typing import Any

import factory
from django.utils import timezone
from faker import Faker

from promise_tracker.classifiers.tests.factories import ValidConvocationFactory, ValidPoliticalPartyFactory
from promise_tracker.promises.models import Promise, PromiseResult

faker = Faker()


class ValidPromiseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Promise

    name = factory.LazyAttribute(lambda _: faker.unique.sentence()[:100])
    description = factory.LazyAttribute(lambda _: faker.paragraph()[:500])
    sources = factory.LazyAttribute(lambda _: ",".join([faker.url()[:20] for _ in range(3)]))
    date = factory.Faker("date_between", start_date="-5y", end_date="-10d")

    convocation = factory.SubFactory(
        ValidConvocationFactory,
        start_date=factory.LazyAttribute(
            lambda o: faker.date_between(start_date="-10y", end_date=o.factory_parent.date)
        ),
        end_date=factory.LazyAttribute(
            lambda o: (
                faker.date_between(start_date=o.factory_parent.date, end_date="today")
                if o.factory_parent.date <= date.today()
                else o.factory_parent.date
            )
        ),
    )

    @factory.lazy_attribute
    def party(self):
        party = self.convocation.political_parties.first()

        if party is None:
            party = ValidPoliticalPartyFactory.create(
                established_date=(
                    faker.date_between(start_date=self.convocation.start_date, end_date="today")
                    if self.convocation.start_date <= date.today()
                    else self.convocation.start_date
                ),
                liquidated_date=None,
            )
            self.convocation.political_parties.add(party)
        return party

    @factory.post_generation
    def results(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted is not None:
            for result in extracted:
                result.promise = self
                result.save()

        else:
            ValidPromiseResultFactory.create_batch(3, promise=self)


class InvalidPromiseFactory(factory.Factory):
    class Meta:
        model = dict

    name = factory.Faker("lexify", text="?" * 256)
    description = factory.Faker("lexify", text="?" * 2001)
    sources: Any = ",".join([faker.lexify(text="?" * 1001) for _ in range(3)])
    result_status = factory.Faker("word")
    date = factory.Faker("word")

    convocation = faker.word()
    party = faker.word()


class ValidPromiseResultFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PromiseResult

    name = factory.LazyAttribute(lambda _: faker.sentence()[:100])
    description = factory.LazyAttribute(lambda _: faker.paragraph()[:500])
    sources = factory.LazyAttribute(lambda _: ",".join([faker.url()[:20] for _ in range(3)]))
    promise = factory.SubFactory(ValidPromiseFactory)
    is_final = False

    @factory.lazy_attribute
    def date(self):
        promise_date = self.promise.date
        if promise_date > timezone.now().date():
            return promise_date

        return faker.date_between(start_date=promise_date, end_date="today")


class InvalidPromiseResultFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PromiseResult

    name = factory.Faker("lexify", text="?" * 256)
    description = factory.Faker("lexify", text="?" * 2001)
    sources: Any = ",".join([faker.lexify(text="?" * 1001) for _ in range(3)])
    promise = factory.Faker("word")
    is_final = factory.Faker("word")

    date = factory.Faker("word")
