# sqms_apps/notifications.py
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_notification(message, group_name):
    """
    Kirim notifikasi ke grup WebSocket yang ditentukan.
    
    :param message: Pesan yang ingin dikirimkan ke grup
    :param group_name: Nama grup yang menerima pesan (misalnya 'assistants_group', 'manager_group', dll)
    """
    channel_layer = get_channel_layer()
    # Mengirimkan pesan ke grup melalui WebSocket channel layer
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "send_notification",  # type akan diproses di consumer
            "message": message  # Isi pesan yang akan diterima oleh konsumer
        }
    )

# Fungsi spesifik untuk mengirimkan notifikasi ke grup tertentu
def send_notification_to_assistants(message):
    send_notification(message, "assistants_group")

def send_notification_to_manager(message):
    send_notification(message, "manager_group")

def send_notification_to_admin(message):
    send_notification(message, "admin_group")
