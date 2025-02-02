from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class GeosDBBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.using('geos_db').get(username=username)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.using('geos_db').get(pk=user_id)
        except User.DoesNotExist:
            return None
