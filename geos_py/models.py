from django.db import models

class ClientDatabaseManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().using('geospy_db')

class ClientDatabase(models.Model):
    client_name = models.CharField(max_length=255, unique=True)
    db_name     = models.CharField(max_length=255)
    db_user     = models.CharField(max_length=255)
    db_password = models.CharField(max_length=255)
    db_host     = models.CharField(max_length=255)
    db_port     = models.CharField(max_length=255)

    # objects = ClientDatabaseManager()

    def __str__(self):
        return self.client_name