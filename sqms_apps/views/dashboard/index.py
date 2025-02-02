from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from datetime import datetime
from ...utils.permissions import get_dynamic_permissions

def index(request):
    today = datetime.now()
    start_of_month = today.replace(day=1)
    context = {
        'today': today,
        'start_of_month': start_of_month,
        }
  
    return render(request, 'dashboard_mgoqa.html', context)

@login_required
def home_mgoqa(request):
    today = datetime.now()
    start_of_month = today.replace(day=1)
    start_of_day = today  # Anda bisa menggunakan `today` langsung

    # Ambil permissions dinamis dari database
    permissions = get_dynamic_permissions(request.user)

    print("get permissions : ", permissions)
    context = {
        'today': today,
        'start_of_month': start_of_month,
        'start_date'    : today.strftime('%Y-%m-%d'),
        'permissions'   : permissions,

    }

    return render(request, 'dashboard/dashboard_mgoqa.html', context)

@login_required
def home_mining(request):
    today = datetime.today()
    # Ambil permissions dinamis dari database
    permissions = get_dynamic_permissions(request.user)
    context = {
       'start_date': today.strftime('%Y-%m-%d'),
       'permissions'   : permissions,
    }

    return render(request, 'dashboard/dashboard_mining.html',context)

@login_required
def home_vendors(request):
    today = datetime.now()
    start_of_month = today.replace(day=1)
    start_of_day = today  # Anda bisa menggunakan `today` langsung

    return render(request, 'dashboard/dashboard_vendors.html', {
        'start_of_month': start_of_month.isoformat(),  # Konversi ke string
        'start_of_day'  : start_of_day.isoformat()  # Konversi ke string
    })

@login_required
def home_selling(request):
    today = datetime.now()
    start_of_month = today.replace(day=1)
    start_of_day = today  # Anda bisa menggunakan `today` langsung
     # Ambil permissions dinamis dari database
    permissions = get_dynamic_permissions(request.user)
    context = {
        'today': today,
        'start_of_month': start_of_month,
        'start_date'    : today.strftime('%Y-%m-%d'),
         'permissions'   : permissions,
        }
    return render(request, 'dashboard/dashboard_selling.html',context)