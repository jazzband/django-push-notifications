# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('push_notifications', '0004_firefoxdevice'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='firefoxdevice',
            options={'verbose_name': 'Firefox device'},
        ),
    ]
