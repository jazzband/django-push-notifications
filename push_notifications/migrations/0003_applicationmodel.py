# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('push_notifications', '0002_auto_20151125_1555'),
    ]

    operations = [
        migrations.CreateModel(
            name='ApplicationModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('application_id', models.CharField(unique=True, max_length=64, verbose_name='Application ID')),
                ('gcm_api_key', models.TextField(null=True, verbose_name='GCM API Key', blank=True)),
                ('apns_certificate', models.FileField(upload_to='apns_certificates', null=True, verbose_name='APNS Certificate', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
