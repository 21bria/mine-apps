from django.db import models

class ImportReport(models.Model):
    task_id            = models.CharField(max_length=255, unique=True)
    successful_imports = models.IntegerField(default=0)
    failed_imports     = models.IntegerField(default=0)
    duplicate_imports  = models.IntegerField(default=0)
    errors             = models.TextField(blank=True, null=True)
    duplicates         = models.TextField(blank=True, null=True)
    file_name          = models.CharField(max_length=255, null=True, blank=True)
    destination        = models.CharField(max_length=50, null=True, blank=True)
    created_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  = 'task_imports'
        app_label = 'sqms_apps'
        
    def __str__(self):
        return self.name
