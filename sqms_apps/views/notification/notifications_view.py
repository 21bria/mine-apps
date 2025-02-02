from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from ...models.notification_model import Notification

@login_required
def get_notifications(request):
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        data = [
            {
                'id': notif.id,
                'workflow_title': notif.workflow.title,
                'message': notif.message,
                'created_at': notif.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            }
            for notif in notifications
        ]
        return JsonResponse({'notifications': data})
    else:
        return JsonResponse({'notifications': []})
