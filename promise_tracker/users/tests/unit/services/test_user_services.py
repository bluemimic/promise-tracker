from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone
from faker import Faker

from promise_tracker.core.exceptions import ApplicationError, EmailDelayError, NotFoundError, PermissionViolationError
from promise_tracker.users.enums import ModerationAction
from promise_tracker.users.models import BaseUser
from promise_tracker.users.services import UserService
from promise_tracker.users.tests.factories import AdminUserFactory, UnverifiedUserFactory, VerifiedUserFactory

faker = Faker()


class UserServicesUnitTests(TestCase):
    def setUp(self):
        self.service = UserService(
            performed_by=AdminUserFactory.create(),
        )

        self.regular_user_service = UserService(
            performed_by=VerifiedUserFactory.create(),
        )

    def test_check_permission_to_create_admin_raises_error_when_performed_by_not_admin(self):
        with self.assertRaises(PermissionViolationError):
            self.regular_user_service._check_permission_to_create_admin(
                is_admin=True,
            )

    def test_check_permission_to_create_admin_allows_admin_to_create_admin(self):
        try:
            self.service._check_permission_to_create_admin(
                is_admin=True,
            )
        except PermissionViolationError:
            self.fail("create_user() raised PermissionViolationError unexpectedly for admin user!")

    def test_validate_passwords_raises_error_when_passwords_do_not_match(self):
        with self.assertRaisesMessage(
            ApplicationError,
            str(self.service.PASSWORDS_DONT_MATCH),
        ):
            self.service._validate_passwords(
                password="Password123!",
                another_password="DifferentPassword123!",
            )

    def test_validate_passwords_raises_error_when_requirements_not_met(self):
        with self.assertRaises(ApplicationError):
            self.service._validate_passwords(
                password="short",
                another_password="short",
            )

        with self.assertRaises(ApplicationError):
            self.service._validate_passwords(
                password="alllowercasepassword",
                another_password="alllowercasepassword",
            )

        with self.assertRaises(ApplicationError):
            self.service._validate_passwords(
                password="NoDigitsPassword",
                another_password="NoDigitsPassword",
            )

        with self.assertRaises(ApplicationError):
            self.service._validate_passwords(
                password="NoS1mbolsPassword",
                another_password="NoS1mbolsPassword",
            )

    @override_settings(VERIFICATION_CODE_EXPIRY_MINUTES=10)
    def test_handle_verification_generates_code_and_expiry(self):
        new_user = UnverifiedUserFactory.create()

        self.service._handle_verification(new_user)

        self.assertIsNotNone(new_user.verification_code)
        self.assertIsNotNone(new_user.verification_code_expires_at)
        self.assertGreater(
            new_user.verification_code_expires_at,
            timezone.now() + timedelta(minutes=9),
        )
        self.assertLessEqual(
            new_user.verification_code_expires_at,
            timezone.now() + timedelta(minutes=11),
        )

    def test_handle_verification_saves_email_send_time(self):
        new_user = UnverifiedUserFactory.create()

        self.service._handle_verification(new_user)

        self.assertIsNotNone(new_user.verification_email_sent_at)
        self.assertGreaterEqual(
            new_user.verification_email_sent_at,
            timezone.now() - timedelta(seconds=5),
        )
        self.assertLessEqual(
            new_user.verification_email_sent_at,
            timezone.now(),
        )

    def check_check_is_owner_or_admin_raises_error_when_not_owner_nor_admin(self):
        user = VerifiedUserFactory.create()

        non_author_user = VerifiedUserFactory.create()
        service = UserService(
            performed_by=non_author_user,
        )

        with self.assertRaises(PermissionViolationError):
            service._check_is_owner_or_admin(user)

    def test_check_is_owner_or_admin_allows_owner(self):
        user = VerifiedUserFactory.create()

        service = UserService(
            performed_by=user,
        )

        try:
            service._check_is_owner_or_admin(user)
        except PermissionViolationError:
            self.fail("_check_is_owner_or_admin() raised PermissionViolationError unexpectedly for owner user!")

    def test_check_is_owner_or_admin_allows_admin(self):
        user = VerifiedUserFactory.create()

        try:
            self.service._check_is_owner_or_admin(user)
        except PermissionViolationError:
            self.fail("_check_is_owner_or_admin() raised PermissionViolationError unexpectedly for admin user!")

    def test_check_user_is_not_deleted_raises_error_when_user_is_deleted(self):
        user = VerifiedUserFactory.create(is_deleted=True)

        with self.assertRaisesMessage(
            NotFoundError,
            str(self.service.NOT_FOUND_MESSAGE),
        ):
            self.service._check_user_is_not_deleted(user)

    def test_check_user_is_not_deleted_allows_when_user_is_not_deleted(self):
        user = VerifiedUserFactory.create(is_deleted=False)

        try:
            self.service._check_user_is_not_deleted(user)
        except NotFoundError:
            self.fail("_check_user_is_not_deleted() raised NotFoundError unexpectedly for non-deleted user!")

    def test_check_can_edit_inactive_raises_error_when_performed_by_not_admin(self):
        user = VerifiedUserFactory.create(is_active=False)

        with self.assertRaises(PermissionViolationError):
            self.regular_user_service._check_can_edit_inactive(user)

    def test_check_can_edit_inactive_allows_admin(self):
        user = VerifiedUserFactory.create(is_active=False)

        try:
            self.service._check_can_edit_inactive(user)
        except PermissionViolationError:
            self.fail("_check_can_edit_inactive() raised PermissionViolationError unexpectedly for admin user!")

    def test_check_is_already_verified_raises_error_when_user_is_verified(self):
        user = VerifiedUserFactory.create()

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.service.USER_IS_ALREADY_VERIFIED),
        ):
            self.service._check_is_already_verified(user)

    def test_check_is_already_verified_allows_when_user_is_not_verified(self):
        user = UnverifiedUserFactory.create()

        try:
            self.service._check_is_already_verified(user)
        except ApplicationError:
            self.fail("_check_is_already_verified() raised ApplicationError unexpectedly for unverified user!")

    @override_settings(EMAIL_SENDING_DELAY_MINUTES=5)
    def test_check_email_sending_delay_raises_error_when_email_sent_recently(self):
        user = UnverifiedUserFactory.create(
            verification_email_sent_at=timezone.now() - timedelta(minutes=1),
        )

        with self.assertRaises(EmailDelayError):
            self.service._check_email_sending_delay(user)

    @override_settings(EMAIL_SENDING_DELAY_MINUTES=5)
    def test_check_email_sending_delay_allows_when_email_not_sent_recently(self):
        user = UnverifiedUserFactory.create(
            verification_email_sent_at=timezone.now() - timedelta(minutes=10),
        )

        try:
            self.service._check_email_sending_delay(user)
        except EmailDelayError:
            self.fail("_check_email_sending_delay() raised EmailDelayError unexpectedly when email not sent recently!")

    @patch("promise_tracker.users.services.UserService._handle_verification")
    @patch("promise_tracker.users.services.UserService._validate_passwords")
    @patch("promise_tracker.users.services.UserService._check_permission_to_create_admin")
    def test_create_ensures_validations_called(
        self, mock_check_permission, mock_validate_passwords, mock_handle_verification
    ):
        new_user = UnverifiedUserFactory.create()

        with self.assertRaises(ApplicationError):
            self.service.create_user(
                name=new_user.name,
                surname=new_user.surname,
                email=new_user.email,
                username=new_user.username,
                password="short",
                another_password="short",
                is_admin=new_user.is_admin,
            )

        mock_check_permission.assert_called_once_with(new_user.is_admin)
        mock_validate_passwords.assert_called_once_with(
            "short",
            "short",
        )
        mock_handle_verification.assert_called_once()

    def test_create_raises_error_when_email_already_exists(self):
        existing_user = VerifiedUserFactory.create()
        new_user = UnverifiedUserFactory.create()

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.service.UNIQUE_CONSTRAINT_MESSAGE),
        ):
            self.service.create_user(
                name=new_user.name,
                surname=new_user.surname,
                email=existing_user.email,
                username=new_user.username,
                password=new_user.password,
                another_password=new_user.password,
                is_admin=new_user.is_admin,
            )

    def test_create_encode_password(self):
        new_user = UnverifiedUserFactory.create()

        created_user = self.service.create_user(
            name=new_user.name,
            surname=new_user.surname,
            email=faker.unique.email(),
            username=new_user.username,
            password=new_user.password,
            another_password=new_user.password,
            is_admin=new_user.is_admin,
        )

        self.assertNotEqual(created_user.password, new_user.password)
        self.assertTrue(created_user.check_password(new_user.password))

    def test_update_raises_error_when_user_not_found(self):
        user = UnverifiedUserFactory.create()

        with self.assertRaisesMessage(
            NotFoundError,
            str(self.service.NOT_FOUND_MESSAGE),
        ):
            self.service.edit_user(
                id=faker.uuid4(),
                name=user.name,
                surname=user.surname,
                email=user.email,
                username=user.username,
                is_admin=user.is_admin,
            )

    @patch("promise_tracker.users.services.UserService._check_permission_to_create_admin")
    @patch("promise_tracker.users.services.UserService._validate_passwords")
    @patch("promise_tracker.users.services.UserService._check_is_owner_or_admin")
    @patch("promise_tracker.users.services.UserService._check_user_is_not_deleted")
    @patch("promise_tracker.users.services.UserService._check_can_edit_inactive")
    def test_update_ensures_validations_called(
        self,
        mock_check_can_edit_inactive,
        mock_check_user_not_deleted,
        mock_check_is_owner_or_admin,
        mock_validate_passwords,
        mock_check_permission_to_create_admin,
    ):
        user = VerifiedUserFactory.create()

        self.service.edit_user(
            id=user.id,
            name=user.name,
            surname=user.surname,
            email=user.email,
            username=user.username,
            is_admin=user.is_admin,
            password="short",
            another_password="short",
        )

        mock_check_is_owner_or_admin.assert_called_once()
        mock_check_user_not_deleted.assert_called_once()
        mock_check_can_edit_inactive.assert_called_once()
        mock_validate_passwords.assert_called_once_with(
            "short",
            "short",
        )
        mock_check_permission_to_create_admin.assert_called_once()

    @patch("promise_tracker.users.services.UserService._handle_verification")
    def test_update_calls_handle_verification_on_email_change(self, mock_handle_verification):
        user = VerifiedUserFactory.create()

        new_email = faker.unique.email()

        self.service.edit_user(
            id=user.id,
            name=user.name,
            surname=user.surname,
            email=new_email,
            username=user.username,
            is_admin=user.is_admin,
        )

        mock_handle_verification.assert_called_once()

    def test_update_raises_error_when_email_already_exists(self):
        existing_user = VerifiedUserFactory.create()
        user_to_update = VerifiedUserFactory.create()

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.service.UNIQUE_CONSTRAINT_MESSAGE),
        ):
            self.service.edit_user(
                id=user_to_update.id,
                name=user_to_update.name,
                surname=user_to_update.surname,
                email=existing_user.email,
                username=user_to_update.username,
                is_admin=user_to_update.is_admin,
            )

    def test_update_encode_password(self):
        user = VerifiedUserFactory.create()

        password = "NewPassword123!"

        updated_user = self.service.edit_user(
            id=user.id,
            name=user.name,
            surname=user.surname,
            email=user.email,
            username=user.username,
            is_admin=user.is_admin,
            password=password,
            another_password=password,
        )

        self.assertNotEqual(updated_user.password, user.password)
        self.assertTrue(updated_user.check_password(password))

    def test_update_unverify_user_when_new_email(self):
        user = VerifiedUserFactory.create()

        new_email = faker.unique.email()

        updated_user = self.service.edit_user(
            id=user.id,
            name=user.name,
            surname=user.surname,
            email=new_email,
            username=user.username,
            is_admin=user.is_admin,
        )

        self.assertEqual(updated_user.email, new_email)
        self.assertFalse(updated_user.is_verified)

    def test_delete_raises_error_when_user_not_found(self):
        UnverifiedUserFactory.create()

        with self.assertRaisesMessage(
            NotFoundError,
            str(self.service.NOT_FOUND_MESSAGE),
        ):
            self.service.delete_user(
                id=faker.uuid4(),
            )

    @patch("promise_tracker.users.services.UserService._check_is_owner_or_admin")
    @patch("promise_tracker.users.services.UserService._check_user_is_not_deleted")
    @patch("promise_tracker.users.services.UserService._check_can_edit_inactive")
    def test_delete_ensures_validations_called(
        self,
        mock_check_can_edit_inactive,
        mock_check_user_not_deleted,
        mock_check_is_owner_or_admin,
    ):
        user = VerifiedUserFactory.create()

        self.service.delete_user(
            id=user.id,
        )

        mock_check_is_owner_or_admin.assert_called_once()
        mock_check_user_not_deleted.assert_called_once()
        mock_check_can_edit_inactive.assert_called_once()

    def test_delete_anonymize_user(self):
        old_user = VerifiedUserFactory.create()

        self.service.delete_user(
            id=old_user.id,
        )

        user = BaseUser.objects.get(id=old_user.id)

        self.assertTrue(user.is_deleted)
        self.assertNotEqual(user.name, old_user.name)
        self.assertNotEqual(user.surname, old_user.surname)
        self.assertNotEqual(user.email, old_user.email)
        self.assertNotEqual(user.username, old_user.username)

    def test_send_verification_email_raises_error_when_user_not_found(self):
        UnverifiedUserFactory.create()

        with self.assertRaisesMessage(
            NotFoundError,
            str(self.service.NOT_FOUND_MESSAGE),
        ):
            self.service.send_verification_email(
                id=faker.uuid4(),
            )

    @patch("promise_tracker.users.services.UserService._check_is_owner_or_admin")
    @patch("promise_tracker.users.services.UserService._check_user_is_not_deleted")
    @patch("promise_tracker.users.services.UserService._check_can_edit_inactive")
    @patch("promise_tracker.users.services.UserService._check_email_sending_delay")
    @patch("promise_tracker.users.services.UserService._check_is_already_verified")
    @patch("promise_tracker.users.services.UserService._handle_verification")
    def test_send_verification_email_ensures_validations_called(
        self,
        mock_handle_verification,
        mock_check_is_already_verified,
        mock_check_email_sending_delay,
        mock_check_can_edit_inactive,
        mock_check_user_not_deleted,
        mock_check_is_owner_or_admin,
    ):
        user = UnverifiedUserFactory.create()

        self.service.send_verification_email(
            id=user.id,
        )

        mock_check_is_owner_or_admin.assert_called_once()
        mock_check_user_not_deleted.assert_called_once()
        mock_check_can_edit_inactive.assert_called_once()
        mock_check_email_sending_delay.assert_called_once()
        mock_check_is_already_verified.assert_called_once()
        mock_handle_verification.assert_called_once()

    def test_verify_raises_error_when_user_not_found(self):
        user = UnverifiedUserFactory.create()
        verification_code = "123456"

        with self.assertRaisesMessage(
            NotFoundError,
            str(self.service.NOT_FOUND_MESSAGE),
        ):
            self.service.verify_user_email(
                id=faker.uuid4(),
                verification_code=verification_code,
            )

    @patch("promise_tracker.users.services.UserService._check_is_owner_or_admin")
    @patch("promise_tracker.users.services.UserService._check_user_is_not_deleted")
    @patch("promise_tracker.users.services.UserService._check_can_edit_inactive")
    @patch("promise_tracker.users.services.UserService._check_is_already_verified")
    def test_verify_ensures_validations_called(
        self,
        mock_check_is_already_verified,
        mock_check_can_edit_inactive,
        mock_check_user_not_deleted,
        mock_check_is_owner_or_admin,
    ):
        user = UnverifiedUserFactory.create()
        verification_code = "123456"

        with self.assertRaises(ApplicationError):
            self.regular_user_service.verify_user_email(
                id=user.id,
                verification_code=verification_code,
            )

        mock_check_is_owner_or_admin.assert_called_once()
        mock_check_user_not_deleted.assert_called_once()
        mock_check_can_edit_inactive.assert_called_once()
        mock_check_is_already_verified.assert_called_once()

    def test_verify_raises_error_when_code_invalid(self):
        user = UnverifiedUserFactory.create(
            verification_code="654321",
            verification_code_expires_at=timezone.now() + timedelta(minutes=10),
        )
        invalid_code = "123456"

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.service.VERIFICATION_FAILED),
        ):
            self.service.verify_user_email(
                id=user.id,
                verification_code=invalid_code,
            )

    def test_verify_raises_error_when_code_expired(self):
        user = UnverifiedUserFactory.create(
            verification_code="123456",
            verification_code_expires_at=timezone.now() - timedelta(minutes=1),
        )
        verification_code = "123456"

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.service.VERIFICATION_FAILED),
        ):
            self.service.verify_user_email(
                id=user.id,
                verification_code=verification_code,
            )

    def test_verify_marks_user_as_verified(self):
        user = UnverifiedUserFactory.create(
            verification_code="123456",
            verification_code_expires_at=timezone.now() + timedelta(minutes=10),
        )
        verification_code = "123456"

        self.service.verify_user_email(
            id=user.id,
            verification_code=verification_code,
        )

        updated_user = BaseUser.objects.get(id=user.id)

        self.assertTrue(updated_user.is_verified)

    def test_moderate_user_raises_error_when_user_not_found(self):
        VerifiedUserFactory.create()

        with self.assertRaisesMessage(
            NotFoundError,
            str(self.service.NOT_FOUND_MESSAGE),
        ):
            self.service.moderate_user(
                id=faker.uuid4(),
                action=ModerationAction.BAN,
            )

    @patch("promise_tracker.users.services.UserService._check_user_is_not_deleted")
    def test_moderate_user_ensures_validations_called(
        self,
        mock_check_user_not_deleted,
    ):
        user = VerifiedUserFactory.create()

        self.service.moderate_user(
            id=user.id,
            action=ModerationAction.BAN,
        )

        mock_check_user_not_deleted.assert_called_once()

    def test_moderate_user_raises_error_when_ban_and_user_is_not_active(self):
        user = VerifiedUserFactory.create(is_active=False)

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.service.USER_IS_ALREADY_BANNED),
        ):
            self.service.moderate_user(
                id=user.id,
                action=ModerationAction.BAN,
            )

    def test_moderate_user_raises_error_when_unban_and_user_is_active(self):
        user = VerifiedUserFactory.create(is_active=True)

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.service.USER_IS_NOT_BANNED),
        ):
            self.service.moderate_user(
                id=user.id,
                action=ModerationAction.UNBAN,
            )

    def test_moderate_user_changes_user_status(self):
        user = VerifiedUserFactory.create(is_active=True)

        self.service.moderate_user(
            id=user.id,
            action=ModerationAction.BAN,
        )

        banned_user = BaseUser.objects.get(id=user.id)

        self.assertFalse(banned_user.is_active)

        self.service.moderate_user(
            id=user.id,
            action=ModerationAction.UNBAN,
        )

        unbanned_user = BaseUser.objects.get(id=user.id)

        self.assertTrue(unbanned_user.is_active)
