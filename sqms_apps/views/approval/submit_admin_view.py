
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from ...models.workflow_model import Workflow, WorkflowLog
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from ...encrypt_view import encrypt_date, decrypt_date
from ...utils.permissions import get_dynamic_permissions

class submitApprovalProduction(View):
    def post(self, request):
        # Ambil semua data invoice yang valid
        data_list = self._datatables(request)
        return JsonResponse(data_list, safe=False)

    def _datatables(self, request):
        datatables = request.POST
        # Ambil draw
        draw = int(datatables.get('draw'))
        # Ambil start
        start = int(datatables.get('start'))
        # Ambil length (limit)
        length = int(datatables.get('length'))
        # Ambil data search
        search = datatables.get('search[value]')
        # Ambil order column
        order_column = int(datatables.get('order[0][column]'))
        # Ambil order direction
        order_dir = datatables.get('order[0][dir]')

        # Gunakan fungsi get_joined_data
        data = Workflow.objects.all()

        if search:
            data = data.filter(
                Q(status__icontains=search) |
                Q(description__icontains=search) 
            )
       
        # Filter berdasarkan parameter dari request
        startDate = request.POST.get('startDate')
        endDate   = request.POST.get('endDate')
        status    = request.POST.get('status')
        team      = request.POST.get('team')


        if startDate and endDate:
            data = data.filter(date_production__range=[startDate, endDate])

        if status:
            data = data.filter(status=status)

        data = data.filter(team=team)    

        # Atur sorting
        if order_dir == 'desc':
            order_by = f'-{data.model._meta.fields[order_column].name}'
        else:
            order_by = f'{data.model._meta.fields[order_column].name}'

        data = data.order_by(order_by)

        # Menghitung jumlah total sebelum filter
        records_total = data.count()

        # Menerapkan pagination
        paginator = Paginator(data, length)
        total_pages = paginator.num_pages

        # Menghitung jumlah total setelah filter
        total_records_filtered = paginator.count

        # Atur paginator
        try:
            object_list = paginator.page(start // length + 1).object_list
        except PageNotAnInteger:
            object_list = paginator.page(1).object_list
        except EmptyPage:
            object_list = paginator.page(paginator.num_pages).object_list

        data = [
            {
                "id"             : item.id,
                "date_production": item.date_production, 
                "title"          : item.title, 
                "description"    : item.description, 
                "status"         : item.status,
                "team "          : item.team ,
                "register"       : item.register,
                "updated_at"     : item.updated_at
                } for item in object_list
        ]

        return {
            'draw'           : draw,
            'recordsTotal'   : records_total,
            'recordsFiltered': total_records_filtered,
            'data'           : data,
            'start'          : start,
            'length'         : length,
            'totalPages'     : total_pages,
        }
    
def get_approval_log(request, approval_id):
    logs = WorkflowLog.objects.filter(approval_id=approval_id).order_by('-timestamp')
    log_list = [
        {
            'timestamp' : log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),  # Menggunakan 'timestamp' sebagai nama atribut
            'status'    : log.status,
            'user'      : log.user.username,  # atau `log.user.get_full_name()` jika ingin nama lengkap
            'notes'     : log.notes  # Tambahkan notes
        }
        for log in logs
    ]
    return JsonResponse({'logs': log_list})

def get_approval_gc(request):
    if request.method == 'GET':
        try:
            # Mengambil filter_date yang dienkripsi dari parameter query
            encrypted_date = request.GET.get('filter_date')
            team = 'GC'
            
            # Dekripsi filter_date yang dienkripsi
            filter_date = decrypt_date(encrypted_date)
            
            # Mengambil data Approval berdasarkan filter_date dan team
            item = Workflow.objects.get(date_production=filter_date, team=team)
            
            # Mengambil data log_approval terkait Approval berdasarkan id
            logs = WorkflowLog.objects.filter(approval_id=item.id).order_by('-timestamp')
            log_list = [
                {
                    'timestamp' : log.timestamp.strftime('%Y-%m-%d %H:%M:%S'), 
                    'status'    : log.status,
                    'user'      : log.user.username,  # atau `log.user.get_full_name()` jika ingin nama lengkap
                    'notes'     : log.notes,
                    'comment'   : log.comment
                }
                for log in logs
            ]
            
            # Menggabungkan data Approval dan log_approval
            data = {
                'id'             : item.id,
                'title'          : item.title,
                'description'    : item.description,
                'status'         : item.status,
                'date_production': item.date_production,
                'team'           : item.team,
                'register'       : item.register,
                'logs'           : log_list  # Menambahkan log_list ke dalam respons
            }
            return JsonResponse(data)
        
        except Workflow.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_approval_mining(request):
    if request.method == 'GET':
        try:
            encrypted_date = request.GET.get('filter_date')
            team = 'Mining'
            # Dekripsi filter_date yang dienkripsi
            filter_date = decrypt_date(encrypted_date)

            items = Workflow.objects.get(date_production=filter_date,team=team)

            # Mengambil data log_approval terkait Approval berdasarkan id
            logs = WorkflowLog.objects.filter(approval_id=items.id).order_by('-timestamp')
            log_list = [
                {
                    'timestamp' : log.timestamp.strftime('%Y-%m-%d %H:%M:%S'), 
                    'status'    : log.status,
                    'user'      : log.user.username,  # atau `log.user.get_full_name()` jika ingin nama lengkap
                    'notes'     : log.notes,
                    'comment'   : log.comment
                }
                for log in logs
            ]

            data = {
                'id'             : items.id,
                'title'          : items.title,
                'description'    : items.description, 
                'status'         : items.status,
                'date_production': items.date_production,
                'team'           : items.team,
                'register'       : items.register,
                'logs'           : log_list  # Menambahkan log_list ke dalam respons
        
            }
            return JsonResponse(data)
        except Workflow.DoesNotExist:
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


# ========= create approval html GC ===========
# Admin
@login_required
def submit_approval_gc_page(request):
    allowed_groups = ['superadmin','admin-mgoqa']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        # Jika tidak memiliki izin, arahkan ke halaman error
        context = {
            'error_message': 'You do not have permission to access this page.',
        }
        return render(request, '403.html', context, status=403)
    # Cek permission
    permissions = get_dynamic_permissions(request.user)
    context = {
        'permissions': permissions,
    }
    return render(request, 'approval/list-submit-approval.html',context)

@login_required
def review_approval_page(request):
    return render(request, 'approval/review_create_approval.html')

# Asisten
@login_required
def review_asisten_page(request):
    allowed_groups = ['superadmin','superintendent-mgoqa']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        # Jika tidak memiliki izin, arahkan ke halaman error
        context = {
            'error_message': 'You do not have permission to access this page.',
        }
        return render(request, '403.html', context, status=403)
    # Cek permission
    permissions = get_dynamic_permissions(request.user)
    context = {
        'permissions': permissions,
    }
    
    return render(request, 'approval/list-assistant-approval.html',context)

# Manager
@login_required
def review_manager_page(request):
    allowed_groups = ['superadmin','manager-mgoqa']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        # Jika tidak memiliki izin, arahkan ke halaman error
        context = {
            'error_message': 'You do not have permission to access this page.',
        }
        return render(request, '403.html', context, status=403)
    # Cek permission
    permissions = get_dynamic_permissions(request.user)
    context = {
        'permissions': permissions,
    }
    
    return render(request, 'approval/list-manager-approval.html',context)


# ========= create approval html Mining ==========
# === Admin
@login_required
def submitApproval_page(request):
    allowed_groups = ['superadmin','admin-mining']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        # Jika tidak memiliki izin, arahkan ke halaman error
        context = {
            'error_message': 'You do not have permission to access this page.',
        }
        return render(request, '403.html', context, status=403)
    permissions = get_dynamic_permissions(request.user)
    context = {
        'permissions': permissions,
    }
    
    return render(request, 'admin-mine/approval/list-submit-approval.html',context)

@login_required
def reviewApproval_page(request):
    permissions = get_dynamic_permissions(request.user)
    context = {
        'permissions': permissions,
    }
    
    return render(request, 'admin-mine/approval/review_create_approval.html',context)

# ==== Asisten
@login_required
def reviewAsisten_page(request):
    allowed_groups = ['superadmin','superintendent-mgoqa']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        # Jika tidak memiliki izin, arahkan ke halaman error
        context = {
            'error_message': 'You do not have permission to access this page.',
        }
        return render(request, '403.html', context, status=403)
    
    permissions = get_dynamic_permissions(request.user)

    context = {
        'permissions': permissions,
    }
    
    return render(request, 'admin-mine/approval/list-assistant-approval.html',context)

# === Manager
@login_required
def reviewManager_page(request):
    allowed_groups = ['superadmin','manager-mgoqa']
    if not request.user.groups.filter(name__in=allowed_groups).exists():
        context = {
            'error_message': 'You do not have permission to access this page.',
        }
        return render(request, '403.html', context, status=403)
    permissions = get_dynamic_permissions(request.user)
    context = {
        'permissions': permissions,
    }
    return render(request, 'admin-mine/approval/list-manager-approval.html',context)

