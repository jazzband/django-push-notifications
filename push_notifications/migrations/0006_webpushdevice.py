# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('push_notifications', '0005_applicationid'),
    ]

    operations = [
        migrations.CreateModel(
            name='WebPushDevice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, null=True, verbose_name='Name', blank=True)),
                ('active', models.BooleanField(default=True, help_text='Inactive devices will not be sent notifications', verbose_name='Is active')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Creation date', null=True)),
                ('application_id', models.CharField(help_text='Opaque application identity, should be filled in for multiple key/certificate access', max_length=64, null=True, verbose_name='Application ID', blank=True)),
                ('registration_id', models.TextField(verbose_name='Registration ID')),
                ('p256dh', models.CharField(max_length=88, verbose_name='User public encryption key')),
                ('auth', models.CharField(max_length=24, verbose_name='User auth secret')),
                ('browser', models.CharField(default='CHROME', help_text='Currently only support to Chrome, Firefox and Opera browsers', max_length=10, verbose_name='Browser', choices=[('CHROME', 'Chrome'), ('FIREFOX', 'Firefox'), ('OPERA', 'Opera')])),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'WebPush device',
            },
        ),
    ]
