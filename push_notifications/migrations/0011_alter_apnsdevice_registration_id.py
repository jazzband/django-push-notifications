from django.db import migrations, models

from ..settings import PUSH_NOTIFICATIONS_SETTINGS as SETTINGS

class Migration(migrations.Migration):

    dependencies = [
        ('push_notifications', '0010_alter_gcmdevice_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apnsdevice',
            name='registration_id',
            field=models.CharField(db_index=not SETTINGS['UNIQUE_REG_ID'], unique=SETTINGS['UNIQUE_REG_ID'], max_length=200, verbose_name='Registration ID'),
        ),
    ]
