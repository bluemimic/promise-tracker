
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Convocation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='The unique identifier for the record.', primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, help_text='The date and time when the record was created.', verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='The date and time when the record was last updated.', verbose_name='Updated At')),
                ('name', models.CharField(error_messages={'unique': 'A convocation %(value)s already exists.'}, help_text='The name of the convocation.', max_length=255, unique=True, verbose_name='Name')),
                ('start_date', models.DateField(help_text='The start date of the convocation.', verbose_name='Start Date')),
                ('end_date', models.DateField(blank=True, help_text='The end date of the convocation, if applicable.', null=True, verbose_name='End Date')),
            ],
            options={
                'verbose_name': 'Convocation',
                'verbose_name_plural': 'Convocations',
            },
        ),
        migrations.CreateModel(
            name='PoliticalParty',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='The unique identifier for the record.', primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, help_text='The date and time when the record was created.', verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='The date and time when the record was last updated.', verbose_name='Updated At')),
                ('name', models.CharField(error_messages={'unique': 'A political party %(value)s already exists.'}, help_text='The name of the political party.', max_length=255, unique=True, verbose_name='Name')),
                ('established_date', models.DateField(help_text='The date when the political party was established.', verbose_name='Established Date')),
                ('liquidated_date', models.DateField(blank=True, help_text='The date when the political party was liquidated, if applicable.', null=True, verbose_name='Liquidated Date')),
            ],
            options={
                'verbose_name': 'Political Party',
                'verbose_name_plural': 'Political Parties',
            },
        ),
    ]
