# middleware.py
import threading

thread_local = threading.local()

class DynamicDBMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        db_config = request.session.get('db_config')
        if db_config:
            thread_local.db_settings = db_config
        else:
            thread_local.db_settings = None
        response = self.get_response(request)
        return response

def get_current_db_settings():
    return getattr(thread_local, 'db_settings', None)
