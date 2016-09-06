# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('push_notifications', '0003_wnsdevice'),
    ]

    operations = [
        migrations.CreateModel(
            name='FirefoxDevice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, null=True, verbose_name='Name', blank=True)),
                ('active', models.BooleanField(default=True, help_text='Inactive devices will not be sent notifications', verbose_name='Is active')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Creation date', null=True)),
                ('registration_id', models.TextField(verbose_name='Registration ID')),
                ('device_id', models.CharField(editable=False, max_length=200, blank=True, help_text='Only for compatibility', null=True, verbose_name='Device ID', db_index=True)),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
