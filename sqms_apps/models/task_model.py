from django.db import models
from django.contrib.auth.models import Group
from django.utils.text import slugify

class taskImports(models.Model):
    task_id            = models.CharField(max_length=255, null=True,default=None)
    successful_imports = models.IntegerField(blank=True,default=0)
    failed_imports     = models.IntegerField(blank=True,default=0)
    duplicate_imports  = models.IntegerField(blank=True,default=0)
    errors             = models.TextField(default=None, null=True, blank=True)
    duplicates         = models.TextField(default=None, null=True, blank=True)
    file_name          = models.CharField(max_length=255,default=None, null=True, blank=True)
    destination        = models.CharField(max_length=255,default=None, null=True, blank=True)
    created_at         = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.task_id 

    class Meta:
        db_table  = 'task_imports'
        app_label = 'sqms_apps'

class taskList(models.Model):
    # order_slug   = models.CharField(max_length=50, null=True,default=None)
    order_slug   = models.SlugField(max_length=255, unique=True)
    type_table   = models.CharField(max_length=150, null=True,default=None)
    status       = models.IntegerField(default=None, null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    # Relasi Many-to-Many dengan Group
    allowed_groups = models.ManyToManyField(Group, related_name="allowed_tasks", blank=True)

    def save(self, *args, **kwargs):
        if not self.order_slug:  # Generate slug only if it is not set
            self.order_slug = slugify(self.type_table)
        super().save(*args, **kwargs)
    
    def _is_type_table_changed(self):
        if not self.pk:  
            return False
        original = taskList.objects.filter(pk=self.pk).only('type_table').first()
        return original and original.type_table != self.type_table
    

    def __str__(self):
        return self.order_slug 

    class Meta:
        db_table  = 'task_table_list'
        app_label = 'sqms_apps'

