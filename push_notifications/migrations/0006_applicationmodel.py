# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ('push_notifications', '0005_auto_20161117_1306'),
    ]

    operations = [
        migrations.CreateModel(
            name='ApplicationModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('application_id', models.CharField(unique=True, max_length=64, verbose_name='Application ID')),
                ('gcm_api_key', models.TextField(null=True, verbose_name='GCM API Key', blank=True)),
                ('fcm_api_key', models.TextField(null=True, verbose_name='FCM API Key', blank=True)),
                ('apns_certificate', models.FileField(upload_to='apns_certificates', null=True, verbose_name='APNS Certificate', blank=True)),
                ('wns_package_security_id', models.TextField(null=True, verbose_name='WNS Package Security ID', blank=True)),
                ('wns_secret_key', models.TextField(null=True, verbose_name='WNS Secret Key', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
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
