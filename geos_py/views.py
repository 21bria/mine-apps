# views.py
from django.shortcuts import render, redirect
from django.db import connections, DatabaseError
from .forms import UserDatabaseConfigForm
from .models import ClientDatabase
from django.http import HttpResponse
from .auth import AuthPermission
import logging
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import OperationalError
from django.conf import settings

logger = logging.getLogger(__name__)



# def configure_database(request):
#     if request.method == 'POST':
#         form = UserDatabaseConfigForm(request.POST)
#         if form.is_valid():
#             # Ambil data koneksi dari formulir
#             db_name     = form.cleaned_data['db_name']
#             db_user     = form.cleaned_data['db_user']
#             db_password = form.cleaned_data['db_password']
#             db_host = form.cleaned_data['db_host']
#             db_port = form.cleaned_data['db_port']
            
#             # Setel koneksi dinamis berdasarkan input pengguna
#             request.session['client_name'] = 'dynamic'  # Simpan nama klien ke dalam sesi
#             request.session.modified = True  # Pastikan perubahan sesi disimpan
            
#             # Redirect pengguna ke halaman login setelah koneksi berhasil
#             return redirect('login_page')  # Ganti 'login_page' dengan nama rute yang sesuai
#     else:
#         form = UserDatabaseConfigForm()
    
#     return render(request, 'configure_database.html', {'form': form})

def configure_database(request):
    if request.method == 'POST':
        form = UserDatabaseConfigForm(request.POST)
        if form.is_valid():
            client_name = form.cleaned_data['client_name']
            db_name = form.cleaned_data['db_name']
            db_user = form.cleaned_data['db_user']
            db_password = form.cleaned_data['db_password'] or ''  # default empty string if not provided
            db_host = form.cleaned_data['db_host']
            db_port = form.cleaned_data['db_port'] or ''  # default empty string if not provided

            # Test the database connection for MySQL
            db_settings = {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': db_name,
                'USER': db_user,
                'PASSWORD': db_password,
                'HOST': db_host,
                'PORT': db_port,
                'OPTIONS': {},  # Add this line with an empty dictionary
                'ATOMIC_REQUESTS': True,
                'TIME_ZONE': 'Asia/Makassar',
                'CONN_HEALTH_CHECKS': True,
                'CONN_MAX_AGE': 0,
                'AUTOCOMMIT': True,  # Add this line
            }

            try:
                connections.databases['test_connection'] = db_settings
                test_connection = connections['test_connection']
                test_connection.ensure_connection()
                # Connection successful
                del connections.databases['test_connection']

                # Save the settings to the database
                ClientDatabase.objects.update_or_create(
                    client_name=client_name,
                    defaults={
                        'db_name': db_name,
                        'db_user': db_user,
                        'db_password': db_password,
                        'db_host': db_host,
                        'db_port': db_port,
                    }
                )
                request.session['client_name'] = client_name
                return redirect('login_page')  # Mengarahkan ke halaman server_page
            # except DatabaseError as e:
            #     logger.error(f"Database connection failed: {e}")
            #     form.add_error(None, 'Database connection failed. Please check your settings.')
            except OperationalError as e:
                error_message = str(e)
                logger.error(f"Operational error occurred: {error_message}")
                return JsonResponse({'error': error_message}, status=400)
            except DatabaseError as e:
                error_message = str(e)
                logger.error(f"Database error occurred: {error_message}")
                return JsonResponse({'error': error_message}, status=400)
        else:
            logger.error(f"Form is not valid: {form.errors}")
    else:
        form = UserDatabaseConfigForm()
    return render(request, 'configure_database.html', {'form': form})

def login_page(request):
    # return render(request, 'pages-login.html')
    # Ambil semua data dari model AuthPermission
    permissions = AuthPermission.objects.all()[:1]

    # Ambil nama dari setiap permission dan simpan dalam list
    permission_names = [permission.name for permission in permissions]

    # Cetak nama permission
    # for name in permission_names:
    #     print(name)

    # Kirim data ke template 'pages-login.html'
    return render(request, 'auth/pages-singup.html', {'data': permissions})