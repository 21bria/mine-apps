from django.db import models
class WaybillsTemporary(models.Model):

    sample_id      = models.CharField(max_length=25, default=None, null=True, blank=True)
    id_type_sample = models.BigIntegerField(default=None, null=True, blank=True)
    id_method      = models.BigIntegerField(default=None, null=True, blank=True)
    id_material    = models.IntegerField(default=None, null=True, blank=True)
    sampling_area  = models.BigIntegerField(default=None, null=True, blank=True)
    sampling_point = models.BigIntegerField(default=None, null=True, blank=True)
    batch_code     = models.CharField(max_length=10, default=None, null=True, blank=True)
    no_save        = models.CharField(max_length=15, default=None, null=True, blank=True)
    status_input   = models.CharField(max_length=15, default=None, null=True, blank=True)
    id_user        = models.IntegerField(default=None, null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  = 'waybill_temps'
        app_label = 'sqms_apps'

   
class listTemporary(models.Model):

    sample_id      = models.CharField(max_length=25, default=None, null=True, blank=True)
    type_sample    = models.CharField(max_length=25, default=None, null=True, blank=True)
    sample_method  = models.CharField(max_length=25, default=None, null=True, blank=True)
    nama_material  = models.CharField(max_length=50, default=None, null=True, blank=True)
    sampling_area  = models.CharField(max_length=50, default=None, null=True, blank=True)
    sampling_point = models.CharField(max_length=50, default=None, null=True, blank=True)
    batch_code     = models.CharField(max_length=10, default=None, null=True, blank=True)
    no_save        = models.CharField(max_length=15, default=None, null=True, blank=True)
    status_input   = models.CharField(max_length=15, default=None, null=True, blank=True)
    id_user        = models.IntegerField(default=None, null=True, blank=True)


    class Meta:
        managed   = False
        db_table  = 'waybill_temporary'
        app_label = 'sqms_apps'

   

