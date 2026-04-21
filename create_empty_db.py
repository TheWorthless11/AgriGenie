import os
import django
import sqlite3
import shutil
import sys

# Force new database
db_path = 'db_fresh2.sqlite3'
target_db = 'db.sqlite3'

if os.path.exists(db_path):
    os.remove(db_path)

# Create completely empty database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE django_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app TEXT NOT NULL,
    name TEXT NOT NULL,
    applied TIMESTAMP,
    UNIQUE (app, name)
)
""")
conn.commit()
conn.close()

print(f"Created empty database at {db_path}")

# Now set Django to use this database
os.environ['DB_ENGINE'] = 'django.db.backends.sqlite3'
os.environ['DB_NAME'] = db_path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from django.core.management import call_command

print("\nRunning migrations...")
try:
    call_command('migrate', '--noinput', verbosity=2)
    print("\nMigrations completed successfully!")
    
    # Backup to main db
    shutil.copy(db_path, target_db)
    print(f"\nCopied database from {db_path} to {target_db}")
    
except Exception as e:
    print(f"\nMigration failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
