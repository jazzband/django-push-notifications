# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import push_notifications.fields


class Migration(migrations.Migration):

    dependencies = [
        ('push_notifications', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apnsdevice',
            name='device_id',
            field=models.UUIDField(blank=True, help_text='UDID / UIDevice.identifierForVendor()', null=True, verbose_name='Device ID', db_index=True),
        ),
        migrations.AlterField(
            model_name='gcmdevice',
            name='device_id',
            field=push_notifications.fields.HexIntegerField(help_text='ANDROID_ID / TelephonyManager.getDeviceId() (always as hex)', null=True, verbose_name='Device ID', db_index=True, blank=True),
        ),
    ]
