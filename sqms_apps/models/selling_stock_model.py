from django.db import models

class SellingStockTemp(models.Model):
    temp_stock   = models.CharField(max_length=150, unique=True)
    capasity     = models.FloatField(default=None, null=True, blank=True)
    description  = models.CharField(max_length=255, default=None, null=True, blank=True)
    status       = models.IntegerField(default=None, null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True) 
    updated_at   = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return self.temp_stock

    class Meta:
        db_table  = 'ore_selling_stock_temp'
        app_label = 'sqms_apps'




