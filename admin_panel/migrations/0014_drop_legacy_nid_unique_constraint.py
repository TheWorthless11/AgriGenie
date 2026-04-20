from django.db import migrations


def drop_legacy_nid_unique_constraint(apps, schema_editor):
    # Historical containers may still retain this unique constraint/index
    # even though the app field is no longer unique.
    if schema_editor.connection.vendor != 'postgresql':
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            ALTER TABLE admin_panel_userapproval
            DROP CONSTRAINT IF EXISTS admin_panel_userapproval_nid_number_ee2700cc_uniq;
            """
        )
        cursor.execute(
            """
            DROP INDEX IF EXISTS admin_panel_userapproval_nid_number_ee2700cc_uniq;
            """
        )


class Migration(migrations.Migration):

    dependencies = [
        ('admin_panel', '0013_alter_activitylog_action'),
    ]

    operations = [
        migrations.RunPython(
            drop_legacy_nid_unique_constraint,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
