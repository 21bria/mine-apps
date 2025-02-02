from django.db import connections
from django.db.utils import load_backend
from .models import ClientDatabase
import logging
from pytz import timezone as pytz_timezone
from django.utils import timezone

logger = logging.getLogger(__name__)

class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            user_timezone = request.user.profile.timezone
            if user_timezone:
                timezone.activate(pytz_timezone(user_timezone))
            else:
                timezone.deactivate()
        else:
            timezone.deactivate()
        response = self.get_response(request)
        return response
    
class RequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger.info(f"Request: {request}")
        response = self.get_response(request)
        logger.info(f"Response: {response}")
        return response

class DynamicDBMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/geos_py/'):
            if 'client_name' in request.session:
                client_name = request.session['client_name']
                try:
                    client_db = ClientDatabase.objects.get(client_name=client_name)
                    db_settings = {
                        'ENGINE': 'django.db.backends.mysql',
                        'NAME': client_db.db_name,
                        'USER': client_db.db_user,
                        'PASSWORD': client_db.db_password,
                        'HOST': client_db.db_host,
                        'PORT': client_db.db_port,
                        'OPTIONS': {},  
                        'ATOMIC_REQUESTS': True,
                        'TIME_ZONE': 'Asia/Makassar',
                        'CONN_HEALTH_CHECKS': True,
                        'CONN_MAX_AGE': 0,
                        'AUTOCOMMIT': True, 
                    }
                    connections.databases['default'] = db_settings
                    backend = load_backend(db_settings['ENGINE'])
                    connection = backend.DatabaseWrapper(db_settings, alias='default')
                    connections['default'] = connection
                    response = self.get_response(request)
                    return response
                except ClientDatabase.DoesNotExist:
                    pass
        response = self.get_response(request)
        return response
