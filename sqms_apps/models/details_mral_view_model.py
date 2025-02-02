from django.db import models

class DetailsMral(models.Model):
    tgl_production = models.DateField(default=None, null=True, blank=True)
    category       = models.CharField(max_length=10, default=None, null=True, blank=True)
    shift          = models.CharField(max_length=10, default=None, null=True, blank=True)
    prospect_area  = models.CharField(max_length=50, default=None, null=True, blank=True)
    mine_block     = models.CharField(max_length=10, default=None, null=True, blank=True)
    from_rl        = models.CharField(max_length=15, default=None, null=True, blank=True)
    to_rl          = models.CharField(max_length=15, default=None, null=True, blank=True)
    nama_material  = models.CharField(max_length=50, default=None, null=True, blank=True)
    ore_class      = models.CharField(max_length=15, default=None, null=True, blank=True)
    ni_grade       = models.FloatField(default=None, null=True, blank=True)
    grade_control  = models.CharField(max_length=50, default=None, null=True, blank=True)
    unit_truck     = models.CharField(max_length=15, default=None, null=True, blank=True)
    stockpile      = models.CharField(max_length=50, default=None, null=True, blank=True)
    pile_id        = models.CharField(max_length=50, default=None, null=True, blank=True)
    batch_code     = models.CharField(max_length=10, default=None, null=True, blank=True)
    increment      = models.IntegerField(default=None, null=True, blank=True)
    batch_status   = models.CharField(max_length=25, default=None, null=True, blank=True)
    ritase         = models.IntegerField(default=None, null=True, blank=True)
    tonnage        = models.FloatField(default=None, null=True, blank=True)
    pile_status    = models.CharField(max_length=15, default=None, null=True, blank=True)
    truck_factor   = models.CharField(max_length=15, default=None, null=True, blank=True)
    remarks        = models.CharField(max_length=255, default=None, null=True, blank=True)
    sample_number  = models.CharField(max_length=25, default=None, null=True, blank=True)
    MRAL_Ni        = models.FloatField(default=None, null=True, blank=True)
    MRAL_Co        = models.FloatField(default=None, null=True, blank=True)
    MRAL_Fe2O3     = models.FloatField(default=None, null=True, blank=True)
    MRAL_Fe        = models.FloatField(default=None, null=True, blank=True)
    MRAL_MgO       = models.FloatField(default=None, null=True, blank=True)
    MRAL_SiO2      = models.FloatField(default=None, null=True, blank=True)
    MRAL_SM        = models.FloatField(default=None, null=True, blank=True)
    

    class Meta:
        managed   = False
        db_table  = 'details_mral'
        app_label = 'sqms_apps'

    def __str__(self):
        return self.sample_number