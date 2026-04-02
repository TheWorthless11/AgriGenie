from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_buyerprofile_total_spent'),
    ]

    operations = [
        migrations.AddField(
            model_name='farmerprofile',
            name='nid_number',
            field=models.CharField(default='', help_text='National ID / Identity Card Number', max_length=50, unique=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='farmerprofile',
            name='nid_card_image',
            field=models.ImageField(default='', help_text='Clear photo of NID/Identity Card', upload_to='nid_cards/'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='farmerprofile',
            name='approval_status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending Review'),
                    ('resubmit_requested', 'Resubmit Required'),
                    ('approved', 'Approved'),
                    ('rejected', 'Rejected'),
                ],
                default='pending',
                help_text='Farmer approval status by super admin',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='farmerprofile',
            name='approved_by',
            field=models.ForeignKey(
                blank=True,
                help_text='Admin who approved this farmer',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='approved_farmers',
                to='users.customuser',
            ),
        ),
        migrations.AddField(
            model_name='farmerprofile',
            name='approved_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='farmerprofile',
            name='rejection_reason',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='farmerprofile',
            name='resubmit_requested_reason',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='farmerprofile',
            name='resubmit_requested_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='farmerprofile',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default='2026-04-02 00:00:00'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='farmerprofile',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='farmerprofile',
            name='is_approved',
            field=models.BooleanField(default=False, help_text='Kept for backward compatibility'),
        ),
    ]
