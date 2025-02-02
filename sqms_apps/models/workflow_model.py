from django.db import models
from django.contrib.auth.models import User

class Workflow(models.Model):
    STATUS_CHOICES = (
        ('submitted', 'Submitted'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    title           = models.CharField(max_length=255)
    description     = models.TextField()
    status          = models.CharField(max_length=50,default='submitted')
    date_production = models.DateField(default=None, null=True, blank=True)
    team            = models.CharField(max_length=25,default=None, null=True, blank=True)
    register        = models.CharField(max_length=25,default=None, null=True, blank=True)
    created_by      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_workflows')
    updated_by      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_workflows', null=True, blank=True)
    updated_at      = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table  = 'workflows'
        app_label = 'sqms_apps'

    def __str__(self):
        return f"{self.title} - {self.register}"
    
class WorkflowLog(models.Model):
    approval  = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='logs')
    status    = models.CharField(max_length=50)
    notes     = models.CharField(max_length=255, blank=True,null=True)
    comment   = models.TextField(blank=True,null=True)
    user      = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  = 'workflows_log'
        app_label = 'sqms_apps'
    
    def __str__(self):
        return f"{self.approval.title} - {self.get_status_display()}"
   
