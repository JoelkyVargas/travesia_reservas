import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "travesia_reservas.settings")
application = get_wsgi_application()
