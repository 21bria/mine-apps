from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

class SQMSDBBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        print(f"Trying to authenticate with backend: {self.__class__.__name__}")  # Log untuk memverifikasi backend yang dipanggil
        try:
            # Django Email Login (instead of using username)
            user = User.objects.using('sqms_db').get(email=username)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.using('sqms_db').get(pk=user_id)
        except User.DoesNotExist:
            return None
        
class EmailBackendSQMS(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            return None
        else:
            if user.check_password(password):
                return user
        return None