from django.db import models

class mineProductions(models.Model):
    date_production = models.DateField(default=None, null=True, blank=True)
    vendors         = models.CharField(max_length=25, default=None, null=True, blank=True)
    shift           = models.CharField(max_length=10, default=None, null=True, blank=True)
    loader          = models.CharField(max_length=25, default=None, null=True, blank=True)
    hauler          = models.CharField(max_length=25, default=None, null=True, blank=True)
    hauler_class    = models.CharField(max_length=25, default=None, null=True, blank=True)
    sources_area    = models.BigIntegerField(default=None, null=True, blank=True)
    loading_point   = models.BigIntegerField(default=None, null=True, blank=True)
    dumping_point   = models.BigIntegerField(default=None, null=True, blank=True)
    dome_id         = models.BigIntegerField(default=None, null=True, blank=True)
    distance        = models.CharField(max_length=250, default=None, null=True, blank=True)
    category_mine   = models.CharField(max_length=25, default=None, null=True, blank=True)
    # time_loading    = models.CharField(max_length=25,default=None, null=True, blank=True)
    time_dumping    = models.CharField(max_length=25,default=None, null=True, blank=True)
    time_loading    = models.TimeField(default=None, null=True, blank=True)
    left_loading    = models.CharField(max_length=2,default=None, null=True, blank=True)
    # time_dumping    = models.TimeField(default=None, null=True, blank=True)
    block_id        = models.CharField(max_length=250,default=None, null=True, blank=True)
    from_rl         = models.CharField(max_length=15, default=None, null=True, blank=True)
    to_rl           = models.CharField(max_length=15, default=None, null=True, blank=True)
    id_material     = models.IntegerField(default=None, null=True, blank=True)
    # id_material     = models.ForeignKey(
    #                 Material, 
    #                 on_delete=models.CASCADE, 
    #                 related_name='mine_productions',
    #                 null=True,    # Field ini bisa bernilai NULL di database
    #                 blank=True    # Field ini tidak diwajibkan di form
    #                 )
    ritase          = models.IntegerField(default=None, null=True, blank=True)
    bcm             = models.FloatField(default=None, null=True, blank=True)
    tonnage         = models.FloatField(default=None, null=True, blank=True)
    remarks         = models.TextField(default=None, null=True, blank=True)
    hauler_type     = models.CharField(max_length=15, default=None, null=True, blank=True)
    ref_materials   = models.CharField(max_length=150, default=None, null=True, blank=True)
    no_production   = models.CharField(max_length=150, default=None, null=True, blank=True)
    task_id         = models.CharField(max_length=255, default=None, null=True, blank=True)
    left_date       = models.IntegerField(default=None, null=True, blank=True)
    id_user         = models.IntegerField(default=None, null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table   = 'productions_mines'
        app_label  = 'sqms_apps'

class mineProductionsView(models.Model):
    date_production = models.DateField(default=None, null=True, blank=True)
    shift           = models.CharField(max_length=10, default=None, null=True, blank=True)
    vendors         = models.CharField(max_length=25, default=None, null=True, blank=True)
    loader          = models.CharField(max_length=25, default=None, null=True, blank=True)
    hauler          = models.CharField(max_length=25, default=None, null=True, blank=True)
    hauler_class    = models.CharField(max_length=25, default=None, null=True, blank=True)
    sources_area    = models.CharField(max_length=50, default=None, null=True, blank=True)
    loading_point   = models.CharField(max_length=50, default=None, null=True, blank=True)
    dumping_point   = models.CharField(max_length=50, default=None, null=True, blank=True)
    dome_id         = models.CharField(max_length=50, default=None, null=True, blank=True)
    category_mine   = models.CharField(max_length=25, default=None, null=True, blank=True)
    time_loading    = models.TimeField(default=None, null=True, blank=True)
    time_dumping    = models.TimeField(default=None, null=True, blank=True)
    mine_block      = models.CharField(max_length=25, default=None, null=True, blank=True)
    from_rl         = models.CharField(max_length=15, default=None, null=True, blank=True)
    to_rl           = models.CharField(max_length=15, default=None, null=True, blank=True)
    rl              = models.CharField(max_length=30, default=None, null=True, blank=True)
    nama_material   = models.CharField(max_length=25, default=None, null=True, blank=True)
    ritase          = models.IntegerField(default=None, null=True, blank=True)
    bcm             = models.FloatField(default=None, null=True, blank=True)
    tonnage         = models.FloatField(default=None, null=True, blank=True)
    remarks         = models.TextField(default=None, null=True, blank=True)
    task_id         = models.CharField(max_length=255, default=None, null=True, blank=True)
    left_date       = models.IntegerField(default=None, null=True, blank=True)
    t_load          = models.IntegerField(default=None, null=True, blank=True)
    t_dump          = models.IntegerField(default=None, null=True, blank=True)
    no_production   = models.CharField(max_length=25,default=None, null=True, blank=True)
    hauler_type     = models.CharField(max_length=15, default=None, null=True, blank=True)
    ref_material    = models.CharField(max_length=110, default=None, null=True, blank=True)
    ref_truck       = models.CharField(max_length=125, default=None, null=True, blank=True)
    id_user         = models.IntegerField(default=None, null=True, blank=True)


    class Meta:
        managed    = False
        db_table   = 'mine_productions'
        app_label  = 'sqms_apps'

# Mine Productions Quick
class mineQuickProductions(models.Model):
    date_production = models.DateField(default=None, null=True, blank=True)
    vendors         = models.CharField(max_length=25, default=None, null=True, blank=True)
    shift           = models.CharField(max_length=10, default=None, null=True, blank=True)
    loader          = models.CharField(max_length=25, default=None, null=True, blank=True)
    hauler          = models.CharField(max_length=25, default=None, null=True, blank=True)
    hauler_class    = models.CharField(max_length=25, default=None, null=True, blank=True)
    sources         = models.IntegerField(default=None, null=True, blank=True)
    loading_point   = models.IntegerField(default=None, null=True, blank=True)
    dumping_point   = models.IntegerField(default=None, null=True, blank=True)
    dome_id         = models.IntegerField(default=None, null=True, blank=True)
    distance        = models.CharField(max_length=250, default=None, null=True, blank=True)
    category_mine   = models.CharField(max_length=25, default=None, null=True, blank=True)
    block_id        = models.BigIntegerField(default=None, null=True, blank=True)
    from_rl         = models.CharField(max_length=15, default=None, null=True, blank=True)
    to_rl           = models.CharField(max_length=15, default=None, null=True, blank=True)
    id_material     = models.IntegerField(default=None, null=True, blank=True)
    ritase          = models.IntegerField(default=None, null=True, blank=True)
    bcm             = models.FloatField(default=None, null=True, blank=True)
    tonnage         = models.FloatField(default=None, null=True, blank=True)
    time_loading    = models.CharField(max_length=2,default=None, null=True, blank=True)
    remarks         = models.TextField(default=None, null=True, blank=True)
    hauler_type     = models.CharField(max_length=15, default=None, null=True, blank=True)
    ref_materials   = models.CharField(max_length=150, default=None, null=True, blank=True)
    ref_plan_truck  = models.CharField(max_length=150, default=None, null=True, blank=True)
    task_id         = models.CharField(max_length=255, default=None, null=True, blank=True)
    no_production   = models.CharField(max_length=25, default=None, null=True, blank=True)
    left_date       = models.IntegerField(default=None, null=True, blank=True)
    id_user         = models.IntegerField(default=None, null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table   = 'productions_quick_mines'
        app_label  = 'sqms_apps'

class mineQuickProductionsView(models.Model):
    date_production = models.DateField(default=None, null=True, blank=True)
    vendors         = models.CharField(max_length=25, default=None, null=True, blank=True)
    shift           = models.CharField(max_length=5, default=None, null=True, blank=True)
    loader          = models.CharField(max_length=25, default=None, null=True, blank=True)
    hauler          = models.CharField(max_length=25, default=None, null=True, blank=True)
    hauler_class    = models.CharField(max_length=25, default=None, null=True, blank=True)
    sources_area    = models.CharField(max_length=50, default=None, null=True, blank=True)
    loading_point   = models.CharField(max_length=50, default=None, null=True, blank=True)
    dumping_point   = models.CharField(max_length=50, default=None, null=True, blank=True)
    pile_id         = models.CharField(max_length=50, default=None, null=True, blank=True)
    distance        = models.CharField(max_length=250, default=None, null=True, blank=True)
    category_mine   = models.CharField(max_length=25, default=None, null=True, blank=True)
    mine_block      = models.CharField(max_length=50, default=None, null=True, blank=True)
    from_rl         = models.CharField(max_length=15, default=None, null=True, blank=True)
    to_rl           = models.CharField(max_length=15, default=None, null=True, blank=True)
    rl              = models.CharField(max_length=30, default=None, null=True, blank=True)
    nama_material   = models.CharField(max_length=30, default=None, null=True, blank=True)
    ritase          = models.IntegerField(default=None, null=True, blank=True)
    bcm             = models.FloatField(default=None, null=True, blank=True)
    tonnage         = models.FloatField(default=None, null=True, blank=True)
    bcm_total       = models.FloatField(default=None, null=True, blank=True)
    tonnage_total   = models.FloatField(default=None, null=True, blank=True)
    time_loading    = models.IntegerField(default=None, null=True, blank=True)
    remarks         = models.TextField(default=None, null=True, blank=True)
    hauler_type     = models.CharField(max_length=15, default=None, null=True, blank=True)
    ref_materials   = models.CharField(max_length=150, default=None, null=True, blank=True)
    ref_plan_truck  = models.CharField(max_length=150, default=None, null=True, blank=True)
    no_production   = models.CharField(max_length=25, default=None, null=True, blank=True)
    task_id         = models.CharField(max_length=255, default=None, null=True, blank=True)
    left_date       = models.IntegerField(default=None, null=True, blank=True)

    class Meta:
        managed    = False
        db_table   = 'mine_quick_productions_v'
        app_label  = 'sqms_apps'


