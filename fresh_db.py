import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

# Set custom database name
os.environ['DB_ENGINE'] = 'django.db.backends.sqlite3'
os.environ['DB_NAME'] = 'db_fresh.sqlite3'

django.setup()

from django.db import connection
from django.core.management import call_command

# Try to create a completely fresh database
try:
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM django_migrations")
    count = cursor.fetchone()[0]
    print(f"Database has {count} migration records")
except Exception as e:
    print(f"Database doesn't exist yet or error: {e}")

print("\nRunning migrate --noinput...")
try:
    call_command('migrate', '--noinput')
    print("Migration complete!")
except Exception as e:
    print(f"Migration failed: {e}")
