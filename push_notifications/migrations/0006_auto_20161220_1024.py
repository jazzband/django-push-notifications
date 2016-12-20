# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('push_notifications', '0005_auto_20160909_1035'),
    ]

    operations = [
        migrations.AddField(
            model_name='apnsdevice',
            name='company',
            field=models.CharField(default='', max_length=255, null=True, verbose_name='Company', blank=True),
        ),
        migrations.AddField(
            model_name='firefoxdevice',
            name='company',
            field=models.CharField(default='', max_length=255, null=True, verbose_name='Company', blank=True),
        ),
        migrations.AddField(
            model_name='gcmdevice',
            name='company',
            field=models.CharField(default='', max_length=255, null=True, verbose_name='Company', blank=True),
        ),
        migrations.AddField(
            model_name='wnsdevice',
            name='company',
            field=models.CharField(default='', max_length=255, null=True, verbose_name='Company', blank=True),
        ),
    ]
