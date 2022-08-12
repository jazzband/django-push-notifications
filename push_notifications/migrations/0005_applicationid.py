# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('push_notifications', '0004_fcm'),
    ]

    operations = [
        migrations.AddField(
            model_name='apnsdevice',
            name='application_id',
            field=models.CharField(help_text='Opaque application identity, should be filled in for multiple key/certificate access', max_length=64, null=True, verbose_name='Application ID', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='gcmdevice',
            name='application_id',
            field=models.CharField(help_text='Opaque application identity, should be filled in for multiple key/certificate access', max_length=64, null=True, verbose_name='Application ID', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='wnsdevice',
            name='application_id',
            field=models.CharField(help_text='Opaque application identity, should be filled in for multiple key/certificate access', max_length=64, null=True, verbose_name='Application ID', blank=True),
            preserve_default=True,
        ),
    ]
