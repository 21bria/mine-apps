from django.db import models
from ..models.workflow_model import Workflow
from django.contrib.auth.models import User

class Notification(models.Model):
    user     = models.ForeignKey(User, on_delete=models.CASCADE)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='notifications')
    message  = models.TextField()
    is_read  = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  = 'notifications'
        app_label = 'sqms_apps'

    def __str__(self):
        return f"{self.workflow.title} - {self.message}"