from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


def seed_irrigation_catalog_from_existing_crops(apps, schema_editor):
    IrrigationCrop = apps.get_model('farmer', 'IrrigationCrop')
    IrrigationCropCatalog = apps.get_model('farmer', 'IrrigationCropCatalog')

    if IrrigationCropCatalog.objects.exists():
        return

    seen_names = set()
    for crop in IrrigationCrop.objects.order_by('name'):
        name = str(getattr(crop, 'name', '') or '').strip().lower()
        if not name or name in seen_names:
            continue

        seen_names.add(name)
        IrrigationCropCatalog.objects.create(
            name=name,
            water_requirement=getattr(crop, 'water_requirement', 'medium') or 'medium',
            base_water_liters=float(getattr(crop, 'base_water_liters', 9.0) or 9.0),
            ideal_moisture=int(getattr(crop, 'ideal_moisture', 60) or 60),
            irrigation_frequency_days=int(getattr(crop, 'irrigation_frequency_days', 3) or 3),
            is_active=True,
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('farmer', '0006_irrigationcrop_irrigationschedule_irrigationrecord'),
    ]

    operations = [
        migrations.CreateModel(
            name='IrrigationCropCatalog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('water_requirement', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='medium', max_length=10)),
                ('base_water_liters', models.FloatField(default=9.0, validators=[MinValueValidator(0)])),
                ('ideal_moisture', models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])),
                ('irrigation_frequency_days', models.PositiveSmallIntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(30)])),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Irrigation Crop Catalog',
                'verbose_name_plural': 'Irrigation Crop Catalog',
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='irrigationcrop',
            name='base_water_liters',
            field=models.FloatField(default=9.0, validators=[MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='irrigationcrop',
            name='irrigation_frequency_days',
            field=models.PositiveSmallIntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(30)]),
        ),
        migrations.RunPython(seed_irrigation_catalog_from_existing_crops, noop_reverse),
    ]
