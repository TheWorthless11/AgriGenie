import os
import sys
from pathlib import Path

# Add project to path
project_home = '/home/agrigenie/AgriGenie'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

# Set environment variables for PythonAnywhere
os.environ.setdefault('DEBUG', 'False')
os.environ.setdefault('ALLOWED_HOSTS', 'localhost,127.0.0.1,agrigenie.pythonanywhere.com')
os.environ.setdefault('DATABASE_URL', 'sqlite:////home/agrigenie/AgriGenie/db.sqlite3')

# Import Django
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
