from django.db import models

class planProductions(models.Model):
    date_plan  = models.DateField(default=None, null=True, blank=True)
    category   = models.CharField(max_length=25, default=None, null=True, blank=True)
    sources    = models.CharField(max_length=50, default=None, null=True, blank=True)
    vendors    = models.CharField(max_length=15, default=None, null=True, blank=True)
    TopSoil    = models.FloatField(default=None, null=True, blank=True)
    OB         = models.FloatField(default=None, null=True, blank=True)
    LGLO       = models.FloatField(default=None, null=True, blank=True)
    MGLO       = models.FloatField(default=None, null=True, blank=True)
    HGLO       = models.FloatField(default=None, null=True, blank=True)
    Waste      = models.FloatField(default=None, null=True, blank=True)
    MWS        = models.FloatField(default=None, null=True, blank=True)
    LGSO       = models.FloatField(default=None, null=True, blank=True)
    UGLO       = models.FloatField(default=None, null=True, blank=True)
    MGSO       = models.FloatField(default=None, null=True, blank=True)
    HGSO       = models.FloatField(default=None, null=True, blank=True)
    Quarry     = models.FloatField(default=None, null=True, blank=True)
    Ballast    = models.FloatField(default=None, null=True, blank=True)
    Biomass    = models.FloatField(default=None, null=True, blank=True)
    ref_plan   = models.CharField(max_length=150, default=None, null=True, blank=True)
    task_id    = models.CharField(max_length=255, default=None, null=True, blank=True)
    id_user    = models.IntegerField(default=None, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  = 'plan_productions'
        app_label = 'sqms_apps'

