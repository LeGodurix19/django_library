from django.core.asgi import get_asgi_application
import os
from dotenv import load_dotenv
load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
application = get_asgi_application()

