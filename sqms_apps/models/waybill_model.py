from django.db import models

class Waybills(models.Model):

    tgl_deliver   = models.DateField(default=None, null=True, blank=True)
    delivery_time = models.TimeField(default=None, null=True, blank=True)
    waybill_number= models.CharField(max_length=25, default=None, null=True, blank=True)
    numb_sample   = models.IntegerField(default=None, null=True, blank=True)
    sample_id     = models.CharField(max_length=25, default=None, null=True, blank=True)
    mral_order    = models.CharField(max_length=5, default=None, null=True, blank=True)
    roa_order     = models.CharField(max_length=5, default=None, null=True, blank=True)
    remarks       = models.CharField(max_length=255, default=None, null=True, blank=True)
    left_date     = models.CharField(max_length=2, default=None, null=True, blank=True)
    delivery      = models.DateTimeField(default=None, null=True, blank=True)
    id_user       = models.IntegerField(default=None, null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  = 'waybills'
        app_label = 'sqms_apps'
    
    indexes = [
            models.Index(fields=['sample_id'])
    ]

    @classmethod
    def is_duplicate_data(cls, sample_id):
        return cls.objects.filter(sample_id=sample_id).exists()
   
class listWaybills(models.Model):

    tgl_deliver   = models.DateField(default=None, null=True, blank=True)
    delivery_time = models.TimeField(default=None, null=True, blank=True)
    waybill_number= models.CharField(max_length=25, default=None, null=True, blank=True)
    numb_sample   = models.IntegerField(default=None, null=True, blank=True)
    sample_id     = models.CharField(max_length=25, default=None, null=True, blank=True)
    mral_order    = models.CharField(max_length=5, default=None, null=True, blank=True)
    roa_order     = models.CharField(max_length=5, default=None, null=True, blank=True)
    remarks       = models.CharField(max_length=255, default=None, null=True, blank=True)
    username      = models.CharField(max_length=50,default=None, null=True, blank=True)


    class Meta:
        managed   = False
        db_table  = 'waybills_list'
        app_label = 'sqms_apps'
    


 
