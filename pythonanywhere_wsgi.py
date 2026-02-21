# PythonAnywhere WSGI Configuration
# Yeh file PythonAnywhere ke Web tab mein configure karni hogi

import sys
import os

# ============================================================
# APNA USERNAME YAHAN LIKHO (PythonAnywhere ka)
# ============================================================
YOUR_USERNAME = 'YourPythonAnywhereUsername'   # ← CHANGE THIS
PROJECT_NAME = 'mysite'
# ============================================================

path = f'/home/{YOUR_USERNAME}/{PROJECT_NAME}'
if path not in sys.path:
    sys.path.insert(0, path)

# Production settings use karo
os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings_production'

# Database credentials (PythonAnywhere MySQL)
# Format: YourUsername$DatabaseName
os.environ['DB_NAME'] = f'{YOUR_USERNAME}$school_erp_db'
os.environ['DB_USER'] = YOUR_USERNAME
os.environ['DB_PASSWORD'] = 'YourMySQLPassword'   # ← CHANGE THIS
os.environ['DB_HOST'] = f'{YOUR_USERNAME}.mysql.pythonanywhere-services.com'
os.environ['DB_PORT'] = '3306'

# Secret key (koi bhi random string likho)
os.environ['DJANGO_SECRET_KEY'] = 'your-super-secret-random-key-here-change-this'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
