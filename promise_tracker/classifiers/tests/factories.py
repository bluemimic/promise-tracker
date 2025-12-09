from datetime import date

import factory
from faker import Faker

from promise_tracker.classifiers.models import Convocation, PoliticalParty

faker = Faker()


class ValidPoliticalPartyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PoliticalParty

    name = factory.LazyAttribute(lambda _: faker.sentence()[:50])
    established_date = factory.Faker("date_between", start_date="-30y", end_date="-1y")
    liquidated_date = factory.Faker("date_between", start_date="-1y", end_date="today")


class InvalidPoliticalPartyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PoliticalParty

    name = factory.Faker("lexify", text="?" * 256)
    established_date = factory.Faker("word")
    liquidated_date = factory.Faker("word")


class ValidConvocationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Convocation

    name = factory.LazyAttribute(lambda _: faker.word()[:50])
    start_date = factory.Faker("date_between", start_date="-10y", end_date="-5y")
    end_date = factory.Faker("date_between", start_date="-4y", end_date="-10d")

    @factory.post_generation
    def political_parties(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for party in extracted:
                self.political_parties.add(party)
        else:
            party = ValidPoliticalPartyFactory.create(
                established_date=(
                    faker.date_between(start_date="-10y", end_date=self.start_date)
                    if self.start_date <= date.today()
                    else self.start_date
                ),
                liquidated_date=(
                    faker.date_between(start_date=self.end_date, end_date="today")
                    if self.end_date <= date.today()
                    else self.end_date
                ),
            )
            self.political_parties.add(party)


class InvalidConvocationFactory(factory.Factory):
    class Meta:
        model = Convocation

    name = factory.Faker("lexify", text="?" * 256)
    start_date = factory.Faker("word")
    end_date = factory.Faker("word")
