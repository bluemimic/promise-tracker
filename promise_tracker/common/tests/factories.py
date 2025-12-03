import factory
from rolepermissions.roles import assign_role

from promise_tracker.core.roles import RegisteredUser
from promise_tracker.users.models import BaseUser


class UnverifiedUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BaseUser

    name = "John"
    surname = "Doe"
    email = "john@doe.com"
    username = "johndoe"
    password = factory.django.Password("some2233SSPassword!")

    @factory.post_generation
    def assign_registered_user_role(obj, create, extracted, **kwargs):
        if not create:
            return

        assign_role(obj, RegisteredUser)


class VerifiedUserFactory(UnverifiedUserFactory):
    is_verified = True
