from django.db import migrations, models

from ..settings import PUSH_NOTIFICATIONS_SETTINGS as SETTINGS


class Migration(migrations.Migration):

    dependencies = [
        ('push_notifications', '0006_webpushdevice'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apnsdevice',
            name='registration_id',
            field=models.CharField(max_length=200, unique=SETTINGS['UNIQUE_REG_ID'], verbose_name='Registration ID'),
        ),
        migrations.AlterField(
            model_name='gcmdevice',
            name='registration_id',
            field=models.TextField(unique=SETTINGS['UNIQUE_REG_ID'], verbose_name='Registration ID'),
        ),
        migrations.AlterField(
            model_name='webpushdevice',
            name='registration_id',
            field=models.TextField(unique=SETTINGS['UNIQUE_REG_ID'], verbose_name='Registration ID'),
        ),
        migrations.AlterField(
            model_name='wnsdevice',
            name='registration_id',
            field=models.TextField(unique=SETTINGS['UNIQUE_REG_ID'], verbose_name='Notification URI'),
        ),
    ]
