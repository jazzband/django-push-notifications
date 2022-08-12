# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import migrations, models

import push_notifications.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='APNSDevice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, null=True, verbose_name='Name', blank=True)),
                ('active', models.BooleanField(default=True, help_text='Inactive devices will not be sent notifications', verbose_name='Is active')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Creation date', null=True)),
                ('device_id', models.UUIDField(help_text='UDID / UIDevice.identifierForVendor()', max_length=32, null=True, verbose_name='Device ID', blank=True, db_index=True)),
                ('registration_id', models.CharField(unique=True, max_length=64, verbose_name='Registration ID')),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'APNS device',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GCMDevice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, null=True, verbose_name='Name', blank=True)),
                ('active', models.BooleanField(default=True, help_text='Inactive devices will not be sent notifications', verbose_name='Is active')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Creation date', null=True)),
                ('device_id', push_notifications.fields.HexIntegerField(help_text='ANDROID_ID / TelephonyManager.getDeviceId() (always as hex)', null=True, verbose_name='Device ID', blank=True, db_index=True)),
                ('registration_id', models.TextField(verbose_name='Registration ID')),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'GCM device',
            },
            bases=(models.Model,),
        ),
    ]
