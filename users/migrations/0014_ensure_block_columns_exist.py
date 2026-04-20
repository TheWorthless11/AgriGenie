from django.db import migrations


def _get_existing_columns(schema_editor, table_name):
    with schema_editor.connection.cursor() as cursor:
        description = schema_editor.connection.introspection.get_table_description(cursor, table_name)
    columns = set()
    for col in description:
        name = getattr(col, 'name', None)
        if name is None:
            name = col[0]
        columns.add(str(name).lower())
    return columns


def ensure_block_columns_exist(apps, schema_editor):
    CustomUser = apps.get_model('users', 'CustomUser')
    table_name = CustomUser._meta.db_table
    vendor = schema_editor.connection.vendor

    columns = _get_existing_columns(schema_editor, table_name)

    def add_column_if_missing(column_name, sql):
        if column_name not in columns:
            schema_editor.execute(sql)
            columns.add(column_name)

    if vendor == 'sqlite':
        add_column_if_missing(
            'blocked_reason',
            f'ALTER TABLE "{table_name}" ADD COLUMN "blocked_reason" text NULL',
        )
        add_column_if_missing(
            'blocked_date',
            f'ALTER TABLE "{table_name}" ADD COLUMN "blocked_date" datetime NULL',
        )
        add_column_if_missing(
            'is_blocked_by_admin',
            f'ALTER TABLE "{table_name}" ADD COLUMN "is_blocked_by_admin" bool NOT NULL DEFAULT 0',
        )
    else:
        add_column_if_missing(
            'blocked_reason',
            f'ALTER TABLE "{table_name}" ADD COLUMN IF NOT EXISTS "blocked_reason" text NULL',
        )
        add_column_if_missing(
            'blocked_date',
            f'ALTER TABLE "{table_name}" ADD COLUMN IF NOT EXISTS "blocked_date" timestamp with time zone NULL',
        )
        add_column_if_missing(
            'is_blocked_by_admin',
            f'ALTER TABLE "{table_name}" ADD COLUMN IF NOT EXISTS "is_blocked_by_admin" boolean NOT NULL DEFAULT FALSE',
        )

    false_literal = '0' if vendor == 'sqlite' else 'FALSE'

    if 'is_blocked_by_admin' in columns:
        schema_editor.execute(
            f'UPDATE "{table_name}" SET "is_blocked_by_admin" = {false_literal} '
            f'WHERE "is_blocked_by_admin" IS NULL'
        )


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_sync_blocked_fields_state'),
    ]

    operations = [
        migrations.RunPython(ensure_block_columns_exist, migrations.RunPython.noop),
    ]
