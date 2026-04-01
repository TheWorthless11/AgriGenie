from django.db import migrations


def add_default_for_legacy_inspection_status(apps, schema_editor):
    if schema_editor.connection.vendor != 'mysql':
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SHOW TABLES LIKE 'admin_panel_userapproval'")
        if cursor.fetchone() is None:
            return

        cursor.execute("SHOW COLUMNS FROM admin_panel_userapproval LIKE 'inspection_status'")
        column = cursor.fetchone()
        if column is None:
            return

        default_value = column[4]
        if default_value in (None, ''):
            cursor.execute(
                "ALTER TABLE admin_panel_userapproval "
                "MODIFY inspection_status varchar(30) NOT NULL DEFAULT 'pending'"
            )


def noop_reverse(apps, schema_editor):
    # Keep compatibility; no reverse action required.
    return


class Migration(migrations.Migration):

    dependencies = [
        ('admin_panel', '0006_userapproval_buyer_documents'),
    ]

    operations = [
        migrations.RunPython(add_default_for_legacy_inspection_status, noop_reverse),
    ]
