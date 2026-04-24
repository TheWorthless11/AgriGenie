import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from django.db import connection

# Clear problematic apps and start fresh
cursor = connection.cursor()
problematic_apps = ['users', 'admin_panel', 'account', 'buyer', 'farmer', 'chat', 'marketplace', 'payment']

for app in problematic_apps:
    try:
        cursor.execute("DELETE FROM django_migrations WHERE app=%s", [app])
        print(f"Cleared migrations for app: {app}")
    except Exception as e:
        print(f"Error clearing {app}: {e}")

connection.commit()
print("\nAll problematic app migrations cleared")
