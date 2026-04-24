import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

import sqlite3
from django.db import connections

#conn = connections['default']
db_path = 'db.sqlite3'

sqlite_conn = sqlite3.connect(db_path)
cursor = sqlite_conn.cursor()

# Check payment tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'payment%'")
tables = cursor.fetchall()

print("Payment tables created:")
for table in tables:
    print(f"  {table[0]}")
    
    # Get column info
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    print(f"    Columns ({len(columns)}):")
    for col in columns:
        print(f"      {col[1]}: {col[2]}")

print(f"\nTotal payment tables: {len(tables)}")

sqlite_conn.close()
