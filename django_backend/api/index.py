import os
import sys

# make sure Django can find our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ipfs_backend.settings')

from django.core.wsgi import get_wsgi_application
app = get_wsgi_application()
