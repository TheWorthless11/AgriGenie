# Generated migration to add mandatory crops (Potato, Tomato, Rice)

from django.db import migrations


def add_mandatory_crops(apps, schema_editor):
    """Add three mandatory crops that farmers must select from"""
    MasterCrop = apps.get_model('admin_panel', 'MasterCrop')
    
    crops_data = [
        {
            'crop_name': 'Potato',
            'crop_type': 'conventional',
            'category': 'vegetables',
            'description': 'Potato crop - starchy vegetable widely grown and traded',
            'is_active': True,
        },
        {
            'crop_name': 'Tomato',
            'crop_type': 'conventional',
            'category': 'vegetables',
            'description': 'Tomato crop - widely used vegetable in cooking',
            'is_active': True,
        },
        {
            'crop_name': 'Rice',
            'crop_type': 'conventional',
            'category': 'grains',
            'description': 'Rice crop - staple grain crop',
            'is_active': True,
        },
    ]
    
    for crop_data in crops_data:
        # Only create if doesn't already exist
        if not MasterCrop.objects.filter(crop_name=crop_data['crop_name']).exists():
            MasterCrop.objects.create(**crop_data)


def reverse_mandatory_crops(apps, schema_editor):
    """Remove mandatory crops if migration is reversed"""
    MasterCrop = apps.get_model('admin_panel', 'MasterCrop')
    MasterCrop.objects.filter(crop_name__in=['Potato', 'Tomato', 'Rice']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('admin_panel', '0003_farmerlisting'),
    ]

    operations = [
        migrations.RunPython(add_mandatory_crops, reverse_mandatory_crops),
    ]
