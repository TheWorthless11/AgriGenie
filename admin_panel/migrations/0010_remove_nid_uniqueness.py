# Generated migration to remove unique constraint from nid_number
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_panel', '0009_alter_userapproval_nid_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userapproval',
            name='nid_number',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
