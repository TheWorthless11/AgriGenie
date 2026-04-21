import os
import django

os.environ['DB_ENGINE'] = 'django.db.backends.sqlite3'
os.environ['DB_NAME'] = 'db_fresh2.sqlite3'

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from django.conf import settings
from django.db import connections

print("DATABASES configuration:")
for key, db_config in settings.DATABASES.items():
    print(f"\n{key}:")
    print(f"  ENGINE: {db_config['ENGINE']}")
    print(f"  NAME: {db_config['NAME']}")

print("\n\nActual database connection:")
conn = connections['default']
print(f"  Vendor: {conn.vendor}")
print(f"  Settings NAME: {conn.settings_dict['NAME']}")

# Check what's in the actual database being used
import sqlite3
db_name = conn.settings_dict['NAME']
print(f"\n\nChecking database file: {db_name}")
print(f"File exists: {os.path.exists(db_name)}")

if os.path.exists(db_name):
    sqlite_conn = sqlite3.connect(db_name)
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT app, name FROM django_migrations ORDER BY id")
    migrations = cursor.fetchall()
    print(f"Migrations in database ({len(migrations)} total):")
    for app, name in migrations[:10]:
        print(f"  {app}.{name}")
    if len(migrations) > 10:
        print(f"  ... and {len(migrations) - 10} more")
