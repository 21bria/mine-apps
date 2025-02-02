from django.db import models

class SellingDomeTemp(models.Model):
    temp_dome    = models.CharField(max_length=150, unique=True)
    capasity     = models.FloatField(default=None, null=True, blank=True)
    description  = models.CharField(max_length=255, default=None, null=True, blank=True)
    status       = models.IntegerField(default=None, null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True) 
    updated_at   = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return self.temp_dome

    class Meta:
        db_table  = 'ore_selling_dome_temp'
        app_label = 'sqms_apps'




