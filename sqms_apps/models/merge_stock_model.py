from django.db import models

class domeMerge(models.Model):
    original_dome   = models.BigIntegerField(default=None,null=True,blank=True)
    stockpile_ori   = models.BigIntegerField(default=None,null=True,blank=True)
    tonnage_primary = models.FloatField(default=None,null=True,blank=True)
    dome_second     = models.BigIntegerField(default=None,null=True,blank=True)
    stockpile_second= models.BigIntegerField(default=None,null=True,blank=True)
    tonnage_second  = models.FloatField(default=None,null=True,blank=True)
    ref_id          = models.CharField(max_length=15,default=None,null=True,blank=True)
    status          = models.CharField(max_length=15,default=None,null=True,blank=True)
    remarks         = models.TextField(default=None,null=True,blank=True)
    id_user         = models.IntegerField(default=None,null=True,blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  ='compositing_domes'
        app_label = 'sqms_apps'

class domeMergeView(models.Model):
    dome_primary     = models.CharField(max_length=50, default=None, null=True, blank=True)
    original_dome    = models.BigIntegerField(default=None, null=True, blank=True)
    stockpile        = models.CharField(max_length=50, default=None, null=True, blank=True)
    stockpile_ori    = models.BigIntegerField(default=None, null=True, blank=True)
    tonnage_primary  = models.FloatField( default=None, null=True, blank=True)
    dome_new         = models.CharField(max_length=50, default=None, null=True, blank=True)
    dome_second      = models.BigIntegerField(default=None, null=True, blank=True)
    stockpile_new    = models.CharField(max_length=50, default=None, null=True, blank=True)
    stockpile_second = models.BigIntegerField(default=None, null=True, blank=True)
    tonnage_second   = models.FloatField(default=None, null=True, blank=True)
    sum_tonnage      = models.FloatField( default=None, null=True, blank=True)
    status           = models.CharField(max_length=15, default=None, null=True, blank=True)
    ref_id           = models.CharField(max_length=15, default=None, null=True, blank=True)
    remarks          = models.TextField(default=None, null=True, blank=True)

    class Meta:
        managed     = False
        db_table    = 'compositing_domes_v'
        app_label   = 'sqms_apps'


class stockpileMerge(models.Model):
    stockpile_ori   = models.BigIntegerField(default=None,null=True,blank=True)
    tonnage_primary = models.FloatField(default=None,null=True,blank=True)
    stockpile_second= models.BigIntegerField(default=None,null=True,blank=True)
    tonnage_second  = models.FloatField(default=None,null=True,blank=True)
    ref_id          = models.CharField(max_length=15,default=None,null=True,blank=True)
    status          = models.CharField(max_length=15,default=None,null=True,blank=True)
    remarks         = models.TextField(default=None,null=True,blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  ='compositing_stockpiles'
        app_label = 'sqms_apps'

class stockpileMergeView(models.Model):
    stockpile_ori   = models.BigIntegerField(default=None, null=True, blank=True)
    stockpile       = models.CharField(max_length=50, default=None, null=True, blank=True)
    tonnage_primary = models.FloatField( default=None, null=True, blank=True)
    stockpile_new   = models.CharField(max_length=50, default=None, null=True, blank=True)
    stockpile_second= models.BigIntegerField(default=None, null=True, blank=True)
    tonnage_second  = models.FloatField(default=None, null=True, blank=True)
    sum_tonnage     = models.FloatField( default=None, null=True, blank=True)
    ref_id          = models.CharField(max_length=15, default=None, null=True, blank=True)
    status          = models.CharField(max_length=15, default=None, null=True, blank=True)
    remarks         = models.TextField(default=None, null=True, blank=True)

    class Meta:
        managed     = False
        db_table    = 'compositing_stock_v'
        app_label   = 'sqms_apps'