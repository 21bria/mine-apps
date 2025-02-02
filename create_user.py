import os
from django.conf import settings
from django.contrib.auth.models import User

# Set environment variable DJANGO_SETTINGS_MODULE
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alpha.settings')

# Inisialisasi pengaturan Django
settings.configure()


# Buat pengguna baru
user = User.objects.create_user('bria', 'bria@example.com', 'konawe@2023')

# Pastikan untuk melakukan commit setelah membuat pengguna
from django.db import transaction
transaction.commit()

