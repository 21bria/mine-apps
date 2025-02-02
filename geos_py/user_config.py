from django.db import models
from django.contrib.auth.models import User

class UserDatabaseConfig(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    db_name = models.CharField(max_length=100)
    db_user = models.CharField(max_length=100)
    db_password = models.CharField(max_length=100)
    db_host = models.CharField(max_length=100)
    db_port = models.CharField(max_length=10, default='3306')

    def __str__(self):
        return f'{self.user.username} Database Configuration'
