
import django.db.models.deletion
import promise_tracker.common.validators
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseUser',
            fields=[
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='The unique identifier for the record.', primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, help_text='The date and time when the record was created.', verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='The date and time when the record was last updated.', verbose_name='Updated At')),
                ('is_deleted', models.BooleanField(db_index=True, default=False, help_text='Indicates whether the record has been soft deleted.', verbose_name='Is Deleted')),
                ('name', models.CharField(help_text='The name of the user.', max_length=255, verbose_name='Name')),
                ('surname', models.CharField(help_text='The surname of the user.', max_length=255, verbose_name='Surname')),
                ('email', models.EmailField(error_messages={'unique': 'A user with this email already exists.'}, help_text='The email address of the user.', max_length=255, unique=True, validators=[promise_tracker.common.validators.CustomEmailValidator()], verbose_name='Email address')),
                ('username', models.CharField(help_text='The username of the user.', max_length=255, verbose_name='Username')),
                ('password', models.CharField(help_text='The hashed password of the user.', max_length=255, verbose_name='Password')),
                ('verification_code', models.CharField(blank=True, help_text='The verification code for email verification.', max_length=255, null=True, verbose_name='Verification code')),
                ('verification_code_expires_at', models.DateTimeField(blank=True, help_text='The expiry date and time of the verification code.', null=True, verbose_name='Verification code expiry')),
                ('verification_email_sent_at', models.DateTimeField(blank=True, help_text='The date and time when the verification email was sent.', null=True, verbose_name='Verification email sent at')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active.', verbose_name='Is active?')),
                ('is_admin', models.BooleanField(default=False, help_text='Designates whether the user has admin privileges.', verbose_name='Is admin?')),
                ('is_verified', models.BooleanField(default=False, help_text='Designates whether the user has verified their email address.', verbose_name='Is verified?')),
                ('created_by', models.ForeignKey(blank=True, help_text='The user who created the record.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('updated_by', models.ForeignKey(blank=True, help_text='The user who last updated the record.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
            },
        ),
    ]
