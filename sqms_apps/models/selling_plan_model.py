from django.db import models

class SellingPlan(models.Model):

    plan_date        = models.DateField(default=None, null=True, blank=True)
    type_ore         = models.CharField(max_length=10, default=None, null=True, blank=True)
    type_selling     = models.CharField(max_length=10, default=None, null=True, blank=True)
    tonnage_plan     = models.FloatField(default=None, null=True, blank=True)
    ni_plan          = models.FloatField(default=None, null=True, blank=True)
    ni_hync          = models.FloatField(default=None, null=True, blank=True)
    ni_awk	         = models.FloatField(default=None, null=True, blank=True)
    check_duplicated = models.CharField(max_length=150, default=None, null=True, blank=True)
    description      = models.CharField(max_length=250, default=None, null=True, blank=True)
    left_date        = models.IntegerField(default=None, null=True, blank=True)
    id_user          = models.IntegerField(default=None, null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table   = 'ore_sellings_plan'
        app_label  = 'sqms_apps'
    
    indexes = [
        models.Index(fields=['plan_date']),
        models.Index(fields=['type_selling'])
    ]



class sellingPlanView(models.Model):
    plan_date        = models.DateField(default=None, null=True, blank=True)
    type_ore         = models.CharField(max_length=10, default=None, null=True, blank=True)
    tonnage_plan     = models.FloatField(default=None, null=True, blank=True)
    ni_plan          = models.FloatField(default=None, null=True, blank=True)
    total            = models.FloatField(default=None, null=True, blank=True)
    achiev	         = models.FloatField(default=None, null=True, blank=True)
    total_wmt	     = models.FloatField(default=None, null=True, blank=True)

    class Meta:
        managed    = False
        db_table   = 'selling_plan_view'
        app_label  = 'sqms_apps'
