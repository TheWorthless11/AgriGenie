from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_panel', '0005_userreport'),
    ]

    operations = [
        migrations.AddField(
            model_name='userapproval',
            name='company_photo',
            field=models.ImageField(blank=True, null=True, upload_to='approvals/company/'),
        ),
        migrations.AddField(
            model_name='userapproval',
            name='legal_paper_photo',
            field=models.ImageField(blank=True, null=True, upload_to='approvals/legal/'),
        ),
    ]
