from django.db import migrations, models


def _get_existing_columns(schema_editor, table_name):
    with schema_editor.connection.cursor() as cursor:
        description = schema_editor.connection.introspection.get_table_description(cursor, table_name)
    return {col.name for col in description}


def sync_blocking_fields(apps, schema_editor):
    CustomUser = apps.get_model('users', 'CustomUser')
    table_name = CustomUser._meta.db_table
    existing_columns = _get_existing_columns(schema_editor, table_name)

    fields_to_add = [
        ('blocked_reason', models.TextField(blank=True, null=True)),
        ('blocked_date', models.DateTimeField(blank=True, null=True)),
        ('is_blocked_by_admin', models.BooleanField(default=False)),
    ]

    for field_name, field in fields_to_add:
        if field_name in existing_columns:
            continue
        field.set_attributes_from_name(field_name)
        schema_editor.add_field(CustomUser, field)
        existing_columns.add(field_name)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0012_farmersettings_farmerpaymentmethod'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(sync_blocking_fields, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='customuser',
                    name='blocked_reason',
                    field=models.TextField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='customuser',
                    name='blocked_date',
                    field=models.DateTimeField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='customuser',
                    name='is_blocked_by_admin',
                    field=models.BooleanField(default=False),
                ),
            ],
        ),
    ]
