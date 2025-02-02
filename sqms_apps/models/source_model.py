from django.db import models

# For Mines Sources
class SourceMines(models.Model):
    sources_area = models.CharField(max_length=50, unique=True)
    remarks      = models.CharField(max_length=255, default=None, null=True, blank=True)
    category     = models.CharField(max_length=25, default=None, null=True, blank=True)
    status       = models.IntegerField(default=None, null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.sources_area

    class Meta:
        db_table = 'mine_sources'
        app_label= 'sqms_apps'
    
    indexes = [
        models.Index(fields=['sources_area'])
    ]

class SourceMinesLoading(models.Model):
    loading_point = models.CharField(max_length=50, unique=True)
    remarks       = models.CharField(max_length=255, default=None, null=True, blank=True)
    category      = models.CharField(max_length=25, default=None, null=True, blank=True)
    # id_sources    = models.BigIntegerField(default=None, null=True, blank=True)
    # Define the foreign key relationship
    id_sources    = models.ForeignKey(
        SourceMines, 
        related_name='mine_sources_point_loading_sources_FK',  # Name of the reverse relation from SourceMines to SourceMinesLoading
        on_delete=models.SET_NULL,      # If the related SourceMines instance is deleted, set this to null
        null=True,                      
        blank=True,
        db_column='id_sources'  # Nama kolom yang lebih pendek di database
    )
    status        = models.IntegerField(default=None, null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.loading_point

    class Meta:
        db_table = 'mine_sources_point_loading'
        app_label= 'sqms_apps'
    
    indexes = [
        models.Index(fields=['loading_point'])
    ]

class SourceMinesDumping(models.Model):
    dumping_point = models.CharField(max_length=50, unique=True)
    remarks       = models.CharField(max_length=255, default=None, null=True, blank=True)
    category      = models.CharField(max_length=25, default=None, null=True, blank=True)
    compositing   = models.CharField(max_length=5, default=None, null=True, blank=True)
    status        = models.IntegerField(default=None, null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.dumping_point

    class Meta:
        db_table = 'mine_sources_point_dumping'
        app_label= 'sqms_apps'

    indexes = [
        models.Index(fields=['dumping_point'])
    ]

class SourceMinesDome(models.Model):
    pile_id     = models.CharField(max_length=50, unique=True)
    remarks     = models.CharField(max_length=255, default=None, null=True, blank=True)
    category    = models.CharField(max_length=25, default=None, null=True, blank=True)
    compositing = models.CharField(max_length=15, default=None, null=True, blank=True)
    dome_finish = models.CharField(max_length=25, default=None, null=True, blank=True)
    status_dome = models.CharField(max_length=15, default=None, null=True, blank=True)
    plan_ni_min = models.FloatField(default=None, null=True, blank=True)
    plan_ni_max = models.FloatField(default=None, null=True, blank=True)
    status      = models.IntegerField(default=None, null=True, blank=True)
    direct_sale = models.CharField(max_length=10,default=None, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.pile_id

    class Meta:
        db_table = 'mine_sources_point_dome'
        app_label= 'sqms_apps'
    
    indexes = [
        models.Index(fields=['pile_id'])
    ]
