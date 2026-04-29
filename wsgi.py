import os, sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.dirname(BASE_DIR))
sys.path.insert(0, os.path.dirname(os.path.dirname(BASE_DIR)))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nodes.acol.settings")

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
