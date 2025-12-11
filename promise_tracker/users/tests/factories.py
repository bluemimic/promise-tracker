import factory
from faker import Faker
from rolepermissions.roles import assign_role

from promise_tracker.core.roles import Administrator, RegisteredUser
from promise_tracker.users.models import BaseUser

fake = Faker()


class UnverifiedUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BaseUser

    name = factory.LazyAttribute(lambda x: fake.unique.name()[:50])
    surname = factory.LazyAttribute(lambda x: fake.last_name()[:50])
    email = factory.LazyAttribute(lambda x: fake.unique.email()[:254])
    username = factory.LazyAttribute(lambda x: fake.user_name()[:150])
    password = factory.django.Password("some2233SSPassword!")
    is_admin = False

    @factory.post_generation
    def assign_registered_user_role(obj, create, extracted, **kwargs):
        if not create:
            return

        assign_role(obj, RegisteredUser)


class VerifiedUserFactory(UnverifiedUserFactory):
    is_verified = True


class AdminUserFactory(VerifiedUserFactory):
    is_admin = True

    @factory.post_generation
    def assign_admin_role(obj, create, extracted, **kwargs):
        if not create:
            return

        assign_role(obj, Administrator)
