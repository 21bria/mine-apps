from django.db import models

class productionReconciliation(models.Model):
    production_date = models.DateTimeField(auto_now_add=True)
    status_gc       = models.CharField(max_length=5)
    gc_status       = models.CharField(max_length=50)
    mining_status   = models.CharField(max_length=50)
    status_mining   = models.CharField(max_length=9)

    class Meta:
        managed   = False
        db_table  = 'production_reconciliation'
        app_label = 'sqms_apps'

    def __str__(self):
        return self.production_date   