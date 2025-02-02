# middleware.py
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import logout

class AutoLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            last_activity = request.session.get('last_activity')

            if last_activity:
                last_activity_time = timezone.datetime.fromisoformat(last_activity)  # Konversi dari string ke datetime
                if (timezone.now() - last_activity_time).total_seconds() > settings.SESSION_COOKIE_AGE:
                    logout(request)
                else:
                    request.session['last_activity'] = timezone.now().isoformat()  # Simpan sebagai string
            else:
                request.session['last_activity'] = timezone.now().isoformat()  # Simpan sebagai string

        response = self.get_response(request)
        return response
