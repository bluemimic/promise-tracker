import factory
from faker import Faker
from rolepermissions.roles import assign_role

from promise_tracker.core.roles import Administrator, RegisteredUser
from promise_tracker.users.models import BaseUser


class UniversalUnverifiedUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BaseUser

    name = factory.LazyAttribute(lambda x: Faker().first_name())
    surname = factory.LazyAttribute(lambda x: Faker().last_name())
    email = factory.LazyAttribute(lambda x: Faker().email())
    username = factory.LazyAttribute(lambda x: Faker().user_name())
    password = factory.django.Password("some2233SSPassword!")
    is_active = True
    is_verified = False
    is_deleted = False
    is_admin = False

    @factory.post_generation
    def assign_registered_user_role(obj, create, extracted, **kwargs):
        if not create:
            return

        assign_role(obj, RegisteredUser)


class UniversalUserFactory(UniversalUnverifiedUserFactory):
    is_verified = True


class AdministratorUserFactory(UniversalUserFactory):
    is_admin = True

    @factory.post_generation
    def assign_admin_role(obj, create, extracted, **kwargs):
        if not create:
            return

        assign_role(obj, Administrator)
