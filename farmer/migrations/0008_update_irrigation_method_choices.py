from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('farmer', '0007_irrigationcropcatalog_and_crop_config_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='irrigationrecord',
            name='method',
            field=models.CharField(
                choices=[
                    ('manual', 'Manual'),
                    ('pump', 'Pump'),
                    ('drip', 'Drip'),
                    ('automatic', 'Automatic (Legacy)'),
                ],
                default='manual',
                max_length=10,
            ),
        ),
    ]
