from django.db import models

class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    codename = models.CharField(max_length=100)

    class Meta:
        db_table = 'auth_permission'

    def __str__(self):
        return self.name