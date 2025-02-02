from django.http import JsonResponse
from cryptography.fernet import Fernet
from django.conf import settings

# For HTML
def encrypt_date_view(request):
    if request.method == 'GET':
        date = request.GET.get('date')
        if date:
            cipher_suite = Fernet(settings.ENCRYPTION_KEY)
            encrypted_date = cipher_suite.encrypt(date.encode()).decode()
            return JsonResponse({'encrypted_date': encrypted_date})
        return JsonResponse({'error': 'No date provided'}, status=400)
    
def encrypt_id_view(request):
    if request.method == 'GET':
        item_id = request.GET.get('id')  # Mengambil 'id' dari query parameter
        if item_id:
            cipher_suite = Fernet(settings.ENCRYPTION_KEY)
            encrypted_id = cipher_suite.encrypt(item_id.encode()).decode()  # Mengenkripsi id
            return JsonResponse({'encrypted_id': encrypted_id})  # Mengembalikan id yang dienkripsi
        return JsonResponse({'error': 'No ID provided'}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)  # Metode tidak valid

def encrypt_date(date):
    cipher_suite = Fernet(settings.ENCRYPTION_KEY)
    encrypted_date = cipher_suite.encrypt(date.encode())
    return encrypted_date.decode()  # Ubah kembali ke string untuk dikirim ke frontend

def decrypt_date(encrypted_date):
    cipher_suite = Fernet(settings.ENCRYPTION_KEY)
    decrypted_date = cipher_suite.decrypt(encrypted_date.encode()).decode()
    return decrypted_date
